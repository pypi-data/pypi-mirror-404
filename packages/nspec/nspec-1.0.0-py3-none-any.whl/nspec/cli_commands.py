"""Nspec CLI Command Handlers - Extracted from cli.main() to reduce complexity.

This module contains individual command handlers for each nspec CLI command,
following the Command pattern to reduce cyclomatic complexity.
"""

import logging
import subprocess
from pathlib import Path
from typing import Protocol

from nspec.crud import (
    add_dependency,
    check_impl_task,
    complete_spec,
    create_new_spec,
    delete_spec,
    next_status,
    remove_dependency,
    set_priority,
    set_status,
    update_epic_loe,
    validate_spec_criteria,
)
from nspec.datasets import DatasetLoader
from nspec.validator import NspecValidator

# Exceptions expected during nspec command operations
_NspecCommandErrors = (RuntimeError, ValueError, KeyError, TypeError, OSError, IOError)


class CommandContext(Protocol):
    """Protocol for command context passed to handlers."""

    # Common attributes
    docs_root: Path
    validator: NspecValidator

    # Command-specific attributes
    validate: bool
    generate: bool
    progress: str | None
    all: bool
    stats: bool
    create_new: bool
    delete: bool
    complete: bool
    force: bool
    check_criteria: bool
    check_task: bool
    validate_criteria: bool
    strict: bool
    criteria_id: str | None
    task_id: str | None
    add_dep: bool
    to: str | None
    dep: str | None
    set_priority: bool
    remove_dep: bool
    title: str | None
    priority: str
    set_status: bool
    next_status: bool
    fr_status: int | None
    impl_status: int | None
    id: str | None
    git_add: bool
    fr_template: str | None
    impl_template: str | None


class CommandHandler:
    """Base class for nspec CLI command handlers."""

    def __init__(self, name: str):
        self.name = name

    def execute(self, context: CommandContext) -> int:
        """Execute the command with the given context."""
        raise NotImplementedError


class ValidateCommandHandler(CommandHandler):
    """Handler for validation command."""

    def __init__(self):
        super().__init__("validate")

    def execute(self, context: CommandContext) -> int:
        """Run validation checks."""
        success, errors = context.validator.validate()

        if success:
            return 0
        else:
            print(f"\n❌ Found {len(errors)} errors:")
            for error in errors:
                print(error)
                print()
            return 1


class GenerateCommandHandler(CommandHandler):
    """Handler for generate command."""

    def __init__(self):
        super().__init__("generate")

    def execute(self, context: CommandContext) -> int:
        """Generate NSPEC.md from validated fRIMPLs."""
        # Pass 1: Validate and compute final sorted datasets
        success, errors = context.validator.validate()

        if not success:
            print(f"\n❌ Validation failed with {len(errors)} errors. Cannot generate.")
            for error in errors:
                print(error)
                print()
            print("Fix errors first, then run --generate again.")
            return 1

        # Pass 2: Auto-update Epic LOE from dependencies
        epic_updates = 0
        for spec_id, fr in context.validator.datasets.active_frs.items():
            if fr.priority.startswith("E"):  # Epic
                try:
                    updated_path = update_epic_loe(spec_id, context.docs_root)
                    if updated_path:
                        epic_updates += 1
                except _NspecCommandErrors as e:
                    logging.warning(f"Failed to update Epic {spec_id}: {e}")

        # Pass 3: Format final sorted datasets to markdown files
        nspec_path = Path("NSPEC.md")
        completed_path = Path("NSPEC_COMPLETED.md")

        context.validator.generate_nspec(nspec_path)
        context.validator.generate_nspec_completed(completed_path)
        return 0


class ProgressCommandHandler(CommandHandler):
    """Handler for progress command."""

    def __init__(self):
        super().__init__("progress")

    def execute(self, context: CommandContext) -> int:
        """Show task/AC progress."""
        # Load datasets
        try:
            loader = DatasetLoader(docs_root=context.docs_root)
            context.validator.datasets = loader.load()
        except ValueError as e:
            print(f"❌ Failed to load datasets: {e}")
            return 1

        if context.progress == "__summary__":
            context.validator.show_progress(show_all=context.all)
        else:
            context.validator.show_progress(spec_id=context.progress)
        return 0


class StatsCommandHandler(CommandHandler):
    """Handler for stats command."""

    def __init__(self):
        super().__init__("stats")

    def execute(self, context: CommandContext) -> int:
        """Show nspec statistics."""
        # Load datasets
        try:
            loader = DatasetLoader(docs_root=context.docs_root)
            context.validator.datasets = loader.load()
        except ValueError as e:
            print(f"❌ Failed to load datasets: {e}")
            return 1

        context.validator.show_stats()
        return 0


class CreateNewCommandHandler(CommandHandler):
    """Handler for create-new command."""

    def __init__(self):
        super().__init__("create-new")

    def execute(self, context: CommandContext) -> int:
        """Create new FR+IMPL from templates."""
        if not context.title:
            print("❌ Error: --title required for --create-new")
            print(
                'Usage: python -m src.tools.nspec --create-new --title "Feature Name" [--priority P2]'
            )
            return 1

        try:
            fr_path, impl_path, spec_id = create_new_spec(
                title=context.title,
                priority=context.priority,
                docs_root=context.docs_root,
                fr_template=context.fr_template,
                impl_template=context.impl_template,
            )

            # Run silent validation to catch issues like ID collisions
            validator = NspecValidator(docs_root=context.docs_root)
            success, errors = validator.validate()
            if not success:
                # Cleanup created files if validation fails
                fr_path.unlink()
                impl_path.unlink()
                print("❌ Created files failed validation (cleaned up):")
                for error in errors:
                    print(f"  {error}")
                return 1

            # Git add if requested
            if context.git_add:
                subprocess.run(["git", "add", str(fr_path), str(impl_path)], check=True)

            # Output just the two file paths (for Make target parsing)
            print(str(fr_path))
            print(str(impl_path))
            return 0
        except (ValueError, FileNotFoundError) as e:
            print(f"❌ Failed to create spec: {e}")
            return 1


class DeleteCommandHandler(CommandHandler):
    """Handler for delete command."""

    def __init__(self):
        super().__init__("delete")

    def execute(self, context: CommandContext) -> int:
        """Delete FR+IMPL for a spec."""
        if not context.id:
            print("❌ Error: --id required for --delete")
            print(
                "Usage: export REALLY_DELETE_NSPEC_ITEM=Y && python -m src.tools.nspec --delete --id XXX"
            )
            return 1

        try:
            fr_path, impl_path = delete_spec(
                spec_id=context.id,
                docs_root=context.docs_root,
            )
            print(f"✅ Deleted Spec {context.id}")
            print(f"   Removed: {fr_path.name}")
            print(f"   Removed: {impl_path.name}")
            return 0
        except (RuntimeError, FileNotFoundError) as e:
            print(f"❌ Failed to delete spec: {e}")
            return 1


class CompleteCommandHandler(CommandHandler):
    """Handler for complete command."""

    def __init__(self):
        super().__init__("complete")

    def execute(self, context: CommandContext) -> int:
        """Move FR+IMPL to completed directory."""
        if not context.id:
            print("❌ Error: --id required for --complete")
            print("Usage: python -m src.tools.nspec --complete --id XXX")
            return 1

        try:
            fr_moved, impl_moved = complete_spec(
                spec_id=context.id,
                docs_root=context.docs_root,
                skip_validation=context.force,
            )
            print(f"✅ Completed Spec {context.id}")
            print(f"   Moved: {fr_moved}")
            print(f"   Moved: {impl_moved}")
            return 0
        except (ValueError, FileNotFoundError) as e:
            print(f"❌ Failed to complete spec: {e}")
            return 1


class AddDependencyCommandHandler(CommandHandler):
    """Handler for add-dep command."""

    def __init__(self):
        super().__init__("add-dep")

    def execute(self, context: CommandContext) -> int:
        """Add dependency to a spec."""
        if not context.to or not context.dep:
            print("❌ Error: --to and --dep required for --add-dep")
            print("Usage: python -m src.tools.nspec --add-dep --to XXX --dep YYY")
            return 1

        try:
            result = add_dependency(
                spec_id=context.to,
                dependency_id=context.dep,
                docs_root=context.docs_root,
            )
            print(f"✅ Added dependency: Spec {context.to} now depends on {context.dep}")
            print(f"   Updated: {result['path']}")
            if result.get("moved_from"):
                print(f"   ↪ Moved from Epic {result['moved_from']}")
            return 0
        except (ValueError, FileNotFoundError) as e:
            print(f"❌ Failed to add dependency: {e}")
            return 1


class RemoveDependencyCommandHandler(CommandHandler):
    """Handler for remove-dep command."""

    def __init__(self):
        super().__init__("remove-dep")

    def execute(self, context: CommandContext) -> int:
        """Remove dependency from a spec."""
        if not context.to or not context.dep:
            print("❌ Error: --to and --dep required for --remove-dep")
            print("Usage: python -m src.tools.nspec --remove-dep --to XXX --dep YYY")
            return 1

        try:
            remove_dependency(
                from_spec_id=context.to,
                to_spec_id=context.dep,
                docs_root=context.docs_root,
            )
            print(f"✅ Removed dependency: Spec {context.to} no longer depends on {context.dep}")
            return 0
        except (ValueError, FileNotFoundError) as e:
            print(f"❌ Failed to remove dependency: {e}")
            return 1


class SetPriorityCommandHandler(CommandHandler):
    """Handler for set-priority command."""

    def __init__(self):
        super().__init__("set-priority")

    def execute(self, context: CommandContext) -> int:
        """Change priority for a spec."""
        if not context.id or not context.priority:
            print("❌ Error: --id and --priority required for --set-priority")
            print("Usage: python -m src.tools.nspec --set-priority --id XXX --priority P1")
            return 1

        try:
            set_priority(
                spec_id=context.id,
                new_priority=context.priority,
                docs_root=context.docs_root,
            )
            print(f"✅ Updated Spec {context.id} priority to {context.priority}")
            return 0
        except (ValueError, FileNotFoundError) as e:
            print(f"❌ Failed to set priority: {e}")
            return 1


class SetStatusCommandHandler(CommandHandler):
    """Handler for _set_frimpl_status command (internal use only)."""

    def __init__(self):
        super().__init__("_set_frimpl_status")

    def execute(self, context: CommandContext) -> int:
        """Set status for FR and IMPL files atomically."""
        if not context.id or context.fr_status is None or context.impl_status is None:
            print(
                "❌ Error: --id, --fr-status, and --impl-status required for --_set_frimpl_status"
            )
            print("   (Internal command - use make nspec.activate or make nspec.next-status)")
            return 1

        try:
            set_status(
                spec_id=context.id,
                fr_status=context.fr_status,
                impl_status=context.impl_status,
                docs_root=context.docs_root,
            )
            print(
                f"✅ Updated Spec {context.id} status (FR={context.fr_status}, IMPL={context.impl_status})"
            )
            return 0
        except (ValueError, FileNotFoundError) as e:
            print(f"❌ Failed to set status: {e}")
            return 1


class NextStatusCommandHandler(CommandHandler):
    """Handler for next-status command."""

    def __init__(self):
        super().__init__("next-status")

    def execute(self, context: CommandContext) -> int:
        """Auto-advance IMPL to next logical state."""
        if not context.id:
            print("❌ Error: --id required for --next-status")
            print("Usage: python -m src.tools.nspec --next-status --id XXX")
            return 1

        try:
            new_statuses = next_status(context.id, context.docs_root)
            print(f"✅ Advanced Spec {context.id} to next status")
            print(f"   FR: {new_statuses['fr']['from']} → {new_statuses['fr']['to']}")
            print(f"   IMPL: {new_statuses['impl']['from']} → {new_statuses['impl']['to']}")
            return 0
        except (ValueError, FileNotFoundError) as e:
            print(f"❌ Failed to advance status: {e}")
            return 1


class CheckCriteriaCommandHandler(CommandHandler):
    """Handler for check-criteria command."""

    def __init__(self):
        super().__init__("check-criteria")

    def execute(self, context: CommandContext) -> int:
        """Mark acceptance criterion as complete."""
        if not context.id or not context.criteria_id:
            print("❌ Error: --id and --criteria-id required for --check-criteria")
            print("Usage: python -m src.tools.nspec --check-criteria --id XXX --criteria-id AC-F1")
            return 1

        try:
            from nspec.crud import check_acceptance_criterion

            check_acceptance_criterion(
                spec_id=context.id,
                criteria_id=context.criteria_id,
                docs_root=context.docs_root,
            )
            print(f"✅ Marked criterion {context.criteria_id} as complete for Spec {context.id}")
            return 0
        except (ValueError, FileNotFoundError) as e:
            print(f"❌ Failed to check criterion: {e}")
            return 1


class CheckTaskCommandHandler(CommandHandler):
    """Handler for check-task command."""

    def __init__(self):
        super().__init__("check-task")

    def execute(self, context: CommandContext) -> int:
        """Mark IMPL task as complete."""
        if not context.id or not context.task_id:
            print("❌ Error: --id and --task-id required for --check-task")
            print('Usage: python -m src.tools.nspec --check-task --id XXX --task-id "1.1"')
            return 1

        try:
            check_impl_task(
                spec_id=context.id,
                task_id=context.task_id,
                docs_root=context.docs_root,
            )
            print(f'✅ Marked task "{context.task_id}" as complete for Spec {context.id}')
            return 0
        except (ValueError, FileNotFoundError) as e:
            print(f"❌ Failed to check task: {e}")
            return 1


class ValidateCriteriaCommandHandler(CommandHandler):
    """Handler for validate-criteria command."""

    def __init__(self):
        super().__init__("validate-criteria")

    def execute(self, context: CommandContext) -> int:
        """Validate acceptance criteria for a spec."""
        if not context.id:
            print("❌ Error: --id required for --validate-criteria")
            print("Usage: python -m src.tools.nspec --validate-criteria --id XXX [--strict]")
            return 1

        try:
            result = validate_spec_criteria(
                spec_id=context.id,
                strict=context.strict,
                docs_root=context.docs_root,
            )

            if result["valid"]:
                print(f"✅ Spec {context.id} criteria validation passed")
                if result["stats"]:
                    print(f"   {result['stats']}")
            else:
                print(f"❌ Spec {context.id} criteria validation failed:")
                for error in result.get("errors", []):
                    print(f"   - {error}")

            return 0 if result["valid"] else 1

        except (ValueError, FileNotFoundError) as e:
            print(f"❌ Failed to validate criteria: {e}")
            return 1


class CommandRegistry:
    """Registry for nspec CLI command handlers."""

    def __init__(self):
        self.handlers: dict[str, CommandHandler] = {}
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Register all built-in command handlers."""
        self.register("validate", ValidateCommandHandler())
        self.register("generate", GenerateCommandHandler())
        self.register("progress", ProgressCommandHandler())
        self.register("stats", StatsCommandHandler())
        self.register("create_new", CreateNewCommandHandler())
        self.register("delete", DeleteCommandHandler())
        self.register("complete", CompleteCommandHandler())
        self.register("add_dep", AddDependencyCommandHandler())
        self.register("remove_dep", RemoveDependencyCommandHandler())
        self.register("set_priority", SetPriorityCommandHandler())
        self.register("set_status", SetStatusCommandHandler())
        self.register("next_status", NextStatusCommandHandler())
        self.register("check_criteria", CheckCriteriaCommandHandler())
        self.register("check_task", CheckTaskCommandHandler())
        self.register("validate_criteria", ValidateCriteriaCommandHandler())

    def register(self, name: str, handler: CommandHandler):
        """Register a command handler."""
        self.handlers[name] = handler

    def get(self, name: str) -> CommandHandler | None:
        """Get a command handler by name."""
        return self.handlers.get(name)

    def execute_from_args(self, context: CommandContext) -> int:
        """Execute the appropriate handler based on parsed arguments."""
        # Check commands in order of precedence
        if context.validate:
            return self.handlers["validate"].execute(context)
        elif context.generate:
            return self.handlers["generate"].execute(context)
        elif context.progress is not None:
            return self.handlers["progress"].execute(context)
        elif context.stats:
            return self.handlers["stats"].execute(context)
        elif context.create_new:
            return self.handlers["create_new"].execute(context)
        elif context.delete:
            return self.handlers["delete"].execute(context)
        elif context.complete:
            return self.handlers["complete"].execute(context)
        elif context.add_dep:
            return self.handlers["add_dep"].execute(context)
        elif context.remove_dep:
            return self.handlers["remove_dep"].execute(context)
        elif context.set_priority:
            return self.handlers["set_priority"].execute(context)
        elif context.set_status:
            return self.handlers["set_status"].execute(context)
        elif context.next_status:
            return self.handlers["next_status"].execute(context)
        elif context.check_criteria:
            return self.handlers["check_criteria"].execute(context)
        elif context.check_task:
            return self.handlers["check_task"].execute(context)
        elif context.validate_criteria:
            return self.handlers["validate_criteria"].execute(context)
        else:
            # Should not reach here if argument validation is correct
            return 1


# Global registry instance
command_registry = CommandRegistry()
