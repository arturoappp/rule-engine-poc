"""
Service layer for rule engine operations.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Union

from app.api.models.rules import Rule as APIRule
from app.api.models.rules import RuleCondition as APIRuleCondition
from rule_engine.core.engine import RuleEngine
from rule_engine.core.failure_info import FailureInfo
from rule_engine.core.rule_result import RuleResult

# Set up logging
logger = logging.getLogger(__name__)




class RuleService:
    """Service for rule engine operations."""

    def __init__(self):
        """Initialize the rule service."""
        self.engine = RuleEngine.get_instance()

    def validate_rule(self, rule: APIRule) -> Tuple[bool, Optional[List[str]]]:
        """
        Validate a rule.

        Args:
            rule: Rule to validate

        Returns:
            Tuple of (valid, errors)
        """
        errors = []

        # Check if conditions are valid
        try:
            # Convert to dictionary and validate - use model_dump() for Pydantic v2
            rule_dict = rule.model_dump(by_alias=True)

            # Check for required fields
            if "name" not in rule_dict or not rule_dict["name"]:
                errors.append("Rule must have a name")

            if "conditions" not in rule_dict or not rule_dict["conditions"]:
                errors.append("Rule must have conditions")
            else:
                # Validate conditions recursively
                condition_errors = self._validate_condition(rule_dict["conditions"])
                errors.extend(condition_errors)

            return len(errors) == 0, errors if errors else None

        except Exception as e:
            logger.error(f"Error validating rule: {e}")
            errors.append(f"Invalid rule format: {str(e)}")
            return False, errors

    def _validate_condition(self, condition: Dict) -> List[str]:
        """
        Validate a condition recursively.

        Args:
            condition: Condition to validate

        Returns:
            List of validation errors
        """
        errors = []

        # If condition is None or not a dict, it's invalid
        if condition is None or not isinstance(condition, dict):
            errors.append("Condition must be a valid object")
            return errors

        # Identify what type of condition we have
        composite_operators = ["all", "any", "none", "not"]
        simple_condition = "path" in condition and condition["path"] is not None
        composite_condition = any(op in condition and condition[op] is not None for op in composite_operators)

        # If neither simple nor composite, it's invalid
        if not simple_condition and not composite_condition:
            errors.append("Condition must be either a simple condition with 'path' or a composite condition")
            return errors

        # Validate composite condition
        if "all" in condition and condition["all"] is not None:
            if not isinstance(condition["all"], list):
                errors.append("'all' must be a list of conditions")
            elif len(condition["all"]) == 0:
                errors.append("'all' must be a non-empty list of conditions")
            else:
                for sub_condition in condition["all"]:
                    errors.extend(self._validate_condition(sub_condition))

        if "any" in condition and condition["any"] is not None:
            if not isinstance(condition["any"], list):
                errors.append("'any' must be a list of conditions")
            elif len(condition["any"]) == 0:
                errors.append("'any' must be a non-empty list of conditions")
            else:
                for sub_condition in condition["any"]:
                    errors.extend(self._validate_condition(sub_condition))

        if "none" in condition and condition["none"] is not None:
            if not isinstance(condition["none"], list):
                errors.append("'none' must be a list of conditions")
            elif len(condition["none"]) == 0:
                errors.append("'none' must be a non-empty list of conditions")
            else:
                for sub_condition in condition["none"]:
                    errors.extend(self._validate_condition(sub_condition))

        if "not" in condition and condition["not"] is not None:
            if not isinstance(condition["not"], dict):
                errors.append("'not' must contain a valid condition object")
            else:
                errors.extend(self._validate_condition(condition["not"]))

        # Validate simple condition
        if simple_condition:
            if "operator" not in condition or not condition["operator"]:
                errors.append("Simple condition must have an 'operator'")
            elif condition["operator"] != "exists" and "value" not in condition:
                errors.append("Simple condition must have a 'value' unless operator is 'exists'")

        return errors

    def get_rule_history(self, limit: int = 10) -> List[Dict]:
        """
        Get information about available rules and their structure.

        En una implementación real, este método podría obtener un historial
        de evaluaciones de una base de datos. Por ahora, proporciona información
        útil sobre las reglas disponibles.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of rule information records
        """
        history = []
        entity_types = self.engine.get_entity_types()

        for entity_type in entity_types:
            categories = self.engine.get_categories(entity_type)

            for category in categories:
                rules = self.engine.get_rules_by_category(entity_type, category)

                for rule in rules:
                    rule_info = {
                        "id": f"{entity_type}-{category}-{rule.get('name', 'unknown')}",
                        "entity_type": entity_type,
                        "category": category,
                        "rule_name": rule.get("name", "Unnamed Rule"),
                        "description": rule.get("description", "No description provided"),
                        "complexity": self._calculate_rule_complexity(rule)
                    }

                    history.append(rule_info)

                    # Limitar la cantidad de registros devueltos
                    if len(history) >= limit:
                        return history

        return history

    def _calculate_rule_complexity(self, rule: Dict) -> Dict:
        """
        Calculate the complexity of a rule based on its structure.

        Args:
            rule: Rule dictionary

        Returns:
            Dictionary with complexity metrics
        """
        if "conditions" not in rule:
            return {"level": "unknown", "conditions": 0, "depth": 0}

        # Contar condiciones y profundidad
        conditions_count = 0
        max_depth = 0

        def count_conditions(cond, depth=0):
            nonlocal conditions_count, max_depth

            if depth > max_depth:
                max_depth = depth

            # Contar condición simple
            if "path" in cond and "operator" in cond:
                conditions_count += 1

            # Contar condiciones compuestas
            for op_type in ["all", "any", "none"]:
                if op_type in cond and isinstance(cond[op_type], list):
                    for subcond in cond[op_type]:
                        count_conditions(subcond, depth + 1)

            # Contar condición "not"
            if "not" in cond and isinstance(cond["not"], dict):
                count_conditions(cond["not"], depth + 1)

        # Iniciar el conteo con las condiciones raíz
        count_conditions(rule["conditions"])

        # Determinar nivel de complejidad
        complexity_level = "simple"
        if conditions_count > 5 or max_depth > 2:
            complexity_level = "moderate"
        if conditions_count > 10 or max_depth > 4:
            complexity_level = "complex"

        return {
            "level": complexity_level,
            "conditions": conditions_count,
            "depth": max_depth
        }

    def export_rules_to_json(self, entity_type: str = None, category: str = None) -> Dict:
        """
        Export rules to a structured JSON format with additional metadata.

        Args:
            entity_type: Optional entity type to filter rules
            category: Optional category to filter rules

        Returns:
            Dictionary with exported rules and metadata
        """
        # Crear un objeto para contener las reglas y metadatos
        result = {
            "metadata": {
                "timestamp": datetime.datetime.now().isoformat(),
                "total_rules": 0,
                "entity_types": [],
                "categories": []
            },
            "rules": {}
        }

        # Obtener los tipos de entidad a exportar
        entity_types = [entity_type] if entity_type else self.engine.get_entity_types()
        result["metadata"]["entity_types"] = entity_types

        all_categories = []
        total_rules = 0

        # Recopilar reglas por tipo de entidad y categoría
        for ent_type in entity_types:
            # Obtener categorías para este tipo de entidad
            if category:
                categories = [category] if category in self.engine.get_categories(ent_type) else []
            else:
                categories = self.engine.get_categories(ent_type)

            all_categories.extend(categories)

            # Inicializar estructura para este tipo de entidad
            result["rules"][ent_type] = {}

            # Obtener reglas para cada categoría
            for cat in categories:
                rules = self.engine.get_rules_by_category(ent_type, cat)

                if rules:
                    result["rules"][ent_type][cat] = rules
                    total_rules += len(rules)

        # Actualizar metadatos
        result["metadata"]["total_rules"] = total_rules
        result["metadata"]["categories"] = list(set(all_categories))

        return result

    def store_rules(self, entity_type: str, rules: List[APIRule], category: str = "default") -> Tuple[bool, str, int]:
        """
        Store rules in the engine, overwriting duplicates with same name.

        Args:
            entity_type: Entity type
            rules: List of rules to store
            category: Optional category

        Returns:
            Tuple of (success, message, stored_rules_count)
        """
        try:
            # Obtener reglas existentes y mapearlas por nombre
            existing_rules = self.engine.get_rules_by_category(entity_type, category)
            existing_rules_dict = {r.get("name", ""): r for r in existing_rules}

            # Contador para reglas nuevas vs sobreescritas
            new_rule_count = 0
            overwritten_rule_count = 0

            # Lista para acumular todas las reglas (nuevas y actualizadas)
            all_rules = []
            processed_rule_names = set()

            # Procesar las nuevas reglas
            for rule in rules:
                # Verificar si la regla ya existe
                if rule.name in existing_rules_dict and rule.name not in processed_rule_names:
                    overwritten_rule_count += 1
                else:
                    new_rule_count += 1

                # Marcar esta regla como procesada
                processed_rule_names.add(rule.name)

                # Añadir la regla a la lista de todas las reglas
                all_rules.append(rule)

            # Añadir reglas existentes que no se están actualizando
            for name, existing_rule in existing_rules_dict.items():
                if name not in processed_rule_names:
                    # Convertir de dict a Rule para consistencia
                    # Aquí usamos asumimos que existing_rule es un dict que podemos pasar a un modelo
                    try:
                        rule_model = APIRule(**existing_rule)
                        all_rules.append(rule_model)
                    except Exception as e:
                        logger.warning(f"Error converting existing rule {name} to model: {e}")

            # Convertir todas las reglas a JSON
            rules_json = json.dumps([
                rule.model_dump(by_alias=True, exclude_none=True)
                for rule in all_rules
            ])

            # Primero borrar todas las reglas existentes para esta categoría y tipo de entidad
            # (Esto depende de cómo tu motor maneja la actualización de reglas)
            # En una implementación real, podrías tener un método para borrar reglas específicas

            # Cargar todas las reglas (las nuevas y las existentes no modificadas)
            self.engine.load_rules_from_json(rules_json, entity_type=entity_type, category=category)

            # Crear mensaje de éxito
            message = f"Successfully stored {len(rules)} rules: "
            if new_rule_count > 0:
                message += f"{new_rule_count} new"
            if new_rule_count > 0 and overwritten_rule_count > 0:
                message += ", "
            if overwritten_rule_count > 0:
                message += f"{overwritten_rule_count} overwritten"

            return True, message, len(rules)

        except Exception as e:
            logger.error(f"Error storing rules: {e}")
            return False, f"Error storing rules: {str(e)}", 0

    def get_rules(self) -> Dict[str, Dict[str, List[Dict]]]:
        """
        Get all rules from the engine.

        Returns:
            Dictionary of rules by entity type and category
        """
        result = {}

        # Get all entity types
        entity_types = self.engine.get_entity_types()

        for entity_type in entity_types:
            result[entity_type] = {}

            # Get all categories for this entity type
            categories = self.engine.get_categories(entity_type)

            for category in categories:
                # Get rules for this category
                rules = self.engine.get_rules_by_category(entity_type, category)
                result[entity_type][category] = rules

        return result

    def evaluate_data(self, data: Dict[str, Any], entity_type: str, categories: Optional[List[str]] = None) -> List[
        RuleResult]:
        """
        Evaluate data against rules.

        Args:
            data: Data to evaluate
            entity_type: Entity type
            categories: Optional list of categories to filter rules

        Returns:
            List of evaluation results
        """
        try:
            return self.engine.evaluate_data(data, entity_type=entity_type, categories=categories)
        except Exception as e:
            logger.error(f"Error evaluating data: {e}")
            raise

    def evaluate_with_rules(self, data: Dict[str, Any], entity_type: str, rules: List[APIRule]) -> List[RuleResult]:
        """
        Evaluate data against provided rules.

        Args:
            data: Data to evaluate
            entity_type: Entity type
            rules: Rules to evaluate against

        Returns:
            List of evaluation results
        """
        try:
            # Create a temporary rule engine
            temp_engine = RuleEngine()

            # Convert rules to JSON - usando model_dump para Pydantic v2
            rules_json = json.dumps([
                rule.model_dump(by_alias=True, exclude_none=True)
                for rule in rules
            ])

            # Debugging para ver la estructura de JSON
            logger.debug(f"Rules JSON: {rules_json}")

            # Load rules into engine
            temp_engine.load_rules_from_json(rules_json, entity_type=entity_type)

            # Evaluate data
            return temp_engine.evaluate_data(data, entity_type=entity_type)
        except Exception as e:
            logger.error(f"Error evaluating data with provided rules: {e}")
            # Return an error result with more detailed failure information
            error_result = RuleResult(
                rule_name=rules[0].name if rules else "Unknown Rule",
                success=False,
                message=f"Error evaluating rule: {str(e)}",
                input_data={"error": str(e)},
                failing_elements=[],
                failure_details=[
                    FailureInfo(
                        operator="unknown",
                        path="$.error",
                        expected_value="valid evaluation",
                        actual_value=str(e)
                    )
                ]
            )
            return [error_result]

    def get_evaluation_stats(self) -> Dict[str, Any]:
        """
        Get statistics about rule evaluation capabilities.

        Returns:
            Statistics about current rule engine configuration
        """
        # Obtener estadísticas basadas en las reglas cargadas actualmente
        entity_types = self.engine.get_entity_types()
        rule_stats = {}
        total_rules = 0

        for entity_type in entity_types:
            categories = self.engine.get_categories(entity_type)
            entity_rule_count = 0
            category_counts = {}

            for category in categories:
                rules = self.engine.get_rules_by_category(entity_type, category)
                category_rule_count = len(rules)
                category_counts[category] = category_rule_count
                entity_rule_count += category_rule_count

            rule_stats[entity_type] = {
                "total_rules": entity_rule_count,
                "categories": category_counts
            }
            total_rules += entity_rule_count

        # Información sobre operadores soportados
        supported_operators = [
            "equal", "not_equal", "greater_than", "less_than",
            "greater_than_equal", "less_than_equal", "exists",
            "not_empty", "match", "contains", "role_device"
        ]

        # Estadísticas sobre el motor de reglas
        engine_stats = {
            "total_rules": total_rules,
            "entity_types": len(entity_types),
            "supported_operators": supported_operators,
            "max_rules_per_request": 100,  # Ejemplo: configurable
            "rule_stats_by_entity": rule_stats
        }

        return engine_stats

    def get_rule_failure_details(self, rule_name: str, entity_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get detailed information about a specific rule, including its structure and validation.

        Args:
            rule_name: Name of the rule to analyze
            entity_type: Optional entity type to filter rules

        Returns:
            Detailed information about the rule
        """
        # Buscar la regla especificada en el motor
        rule_info = None
        rule_entity_type = None
        rule_category = None

        # Buscar en todos los tipos de entidad si no se especifica uno
        search_entity_types = [entity_type] if entity_type else self.engine.get_entity_types()

        for et in search_entity_types:
            categories = self.engine.get_categories(et)
            for category in categories:
                rules = self.engine.get_rules_by_category(et, category)
                for rule in rules:
                    if rule.get("name") == rule_name:
                        rule_info = rule
                        rule_entity_type = et
                        rule_category = category
                        break
                if rule_info:
                    break
            if rule_info:
                break

        if not rule_info:
            return {
                "rule_name": rule_name,
                "found": False,
                "message": f"Rule '{rule_name}' not found in the engine"
            }

        # Analizar la estructura de condiciones de la regla
        def analyze_conditions(conditions, parent_path=""):
            if not conditions:
                return []

            structure = []

            if "path" in conditions and "operator" in conditions:
                # Es una condición simple
                op_info = {
                    "type": "simple",
                    "path": conditions.get("path"),
                    "operator": conditions.get("operator"),
                    "expected_value": conditions.get("value"),
                    "parent_path": parent_path
                }
                structure.append(op_info)

            # Analizar condiciones compuestas
            for op_type in ["all", "any", "none"]:
                if op_type in conditions:
                    for i, subcond in enumerate(conditions[op_type]):
                        new_parent = f"{parent_path}.{op_type}[{i}]" if parent_path else f"{op_type}[{i}]"
                        structure.extend(analyze_conditions(subcond, new_parent))

            if "not" in conditions:
                new_parent = f"{parent_path}.not" if parent_path else "not"
                structure.extend(analyze_conditions(conditions["not"], new_parent))

            return structure

        # Analizar la estructura de la regla
        conditions_structure = analyze_conditions(rule_info.get("conditions", {}))

        # Construir la respuesta
        rule_analysis = {
            "rule_name": rule_name,
            "found": True,
            "entity_type": rule_entity_type,
            "category": rule_category,
            "description": rule_info.get("description"),
            "conditions_count": len(conditions_structure),
            "operators_used": list(set(c["operator"] for c in conditions_structure if "operator" in c)),
            "paths_used": list(set(c["path"] for c in conditions_structure if "path" in c)),
            "structure": conditions_structure,
            "rule_definition": rule_info
        }

        return rule_analysis