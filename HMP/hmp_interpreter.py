"""
HMP Interpreter - Interpretador nativo do protocolo HMP.
"""

import logging
import re
import json
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass

@dataclass
class HMPVariable:
    """Representa uma variável HMP."""
    name: str
    value: Any
    type: str

class HMPInterpreter:
    """
    Interpretador do protocolo HMP (Human-Meaning Protocol).
    Executa código HMP de forma nativa.
    """

    def __init__(self):
        self.variables: Dict[str, HMPVariable] = {}
        self.functions: Dict[str, callable] = {}
        self.execution_log: List[str] = []
        self.call_stack: List[str] = []

        # Registrar funções padrão
        self._register_builtin_functions()

    def _register_builtin_functions(self):
        """Registra funções built-in do HMP."""
        self.functions.update({
            'COMBINE': lambda *args: ' '.join(str(arg) for arg in args),
            'GENERATE_EMBEDDING': lambda text: f"embedding_for_{text}",
            'ANALYZE_REQUEST': self._analyze_request,
            'DECOMPOSE_PROBLEM': self._decompose_problem,
            'GENERATE_EXECUTION_PLAN': self._generate_execution_plan,
            'SYNTHESIZE_RESPONSE': self._synthesize_response,
            'log_info': lambda message: logging.info(f"HMP: {message}"),
            'log_error': lambda message: logging.error(f"HMP: {message}")
        })

    def execute_hmp(self, hmp_code: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executa código HMP e retorna resultado.
        """
        self.execution_log.clear()

        if context:
            for key, value in context.items():
                self.set_variable(key, value, type(value).__name__)

        lines = hmp_code.strip().split('\n')
        result = None

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            try:
                if line.startswith('SET '):
                    self._execute_set(line)
                elif line.startswith('CALL '):
                    result = self._execute_call(line)
                elif line.startswith('IF '):
                    result = self._execute_if(line)
                elif line.startswith('FOR '):
                    result = self._execute_for(line)
                elif line.startswith('RETURN '):
                    result = self._execute_return(line)
                    break
                else:
                    self.execution_log.append(f"Linha ignorada: {line}")

            except Exception as e:
                error_msg = f"Erro na linha {line_num}: {str(e)}"
                self.execution_log.append(error_msg)
                logging.error(error_msg)

        return {
            'result': result,
            'variables': {name: var.value for name, var in self.variables.items()},
            'execution_log': self.execution_log
        }

    def _execute_set(self, line: str):
        """Executa comando SET."""
        match = re.match(r'SET\s+(\w+)\s+TO\s+(.+)', line)
        if match:
            var_name = match.group(1)
            value_expr = match.group(2)
            value = self._evaluate_expression(value_expr)
            self.set_variable(var_name, value)
            self.execution_log.append(f"SET {var_name} = {value}")

    def _execute_call(self, line: str):
        """Executa comando CALL."""
        match = re.match(r'CALL\s+(\w+(?:\.\w+)*)\s+WITH\s+(.+)', line)
        if match:
            func_name = match.group(1)
            params_str = match.group(2)

            if func_name in self.functions:
                # Parse parâmetros simples
                params = self._parse_parameters(params_str)
                result = self.functions[func_name](**params)
                self.execution_log.append(f"CALL {func_name} -> {result}")
                return result
            else:
                self.execution_log.append(f"Função {func_name} não encontrada")
                return None

    def _execute_if(self, line: str):
        """Executa comando IF."""
        match = re.match(r'IF\s+(.+)\s+THEN', line)
        if match:
            condition = match.group(1)
            # Implementação básica de condições
            if self._evaluate_condition(condition):
                self.execution_log.append(f"IF {condition} -> True")
                return True
            else:
                self.execution_log.append(f"IF {condition} -> False")
                return False

    def _execute_for(self, line: str):
        """Executa comando FOR."""
        match = re.match(r'FOR\s+(\w+)\s+IN\s+(.+):', line)
        if match:
            var_name = match.group(1)
            collection_var = match.group(2)
            if collection_var in self.variables:
                return self.variables[collection_var].value

    def _execute_return(self, line: str):
        """Executa comando RETURN."""
        match = re.match(r'RETURN\s+(.+)', line)
        if match:
            value_expr = match.group(1)
            return self._evaluate_expression(value_expr)

    def _evaluate_expression(self, expr: str):
        """Avalia uma expressão HMP."""
        expr = expr.strip()

        # String literals
        if expr.startswith('"') and expr.endswith('"'):
            return expr[1:-1]
        if expr.startswith("'") and expr.endswith("'"):
            return expr[1:-1]

        # Numbers
        try:
            if '.' in expr:
                return float(expr)
            return int(expr)
        except ValueError:
            pass

        # Variables
        if expr in self.variables:
            return self.variables[expr].value

        # Complex expressions
        if '+' in expr:
            parts = expr.split(' + ')
            return sum(self._evaluate_expression(part.strip()) for part in parts if part.strip().isdigit())

        # Default
        return expr

    def _evaluate_condition(self, condition: str) -> bool:
        """Avalia uma condição booleana."""
        condition = condition.strip()

        # Condições simples
        if ' > ' in condition:
            left, right = condition.split(' > ')
            left_val = self._evaluate_expression(left)
            right_val = self._evaluate_expression(right)
            # Garantir comparação de tipos compatíveis
            try:
                # Tentar conversão numérica primeiro
                left_num = float(left_val) if isinstance(left_val, (str, int, float)) else left_val
                right_num = float(right_val) if isinstance(right_val, (str, int, float)) else right_val

                if left_num > right_num:
                    return True
            except (ValueError, TypeError):
                # Fallback para comparação de strings
                left_str = str(left_val)
                right_str = str(right_val)

                if left_str > right_str:
                    return True
        elif ' < ' in condition:
            left, right = condition.split(' < ')
            left_val = self._evaluate_expression(left)
            right_val = self._evaluate_expression(right)
            # Garantir comparação de tipos compatíveis
            try:
                # Tentar conversão numérica primeiro
                left_num = float(left_val) if isinstance(left_val, (str, int, float)) else left_val
                right_num = float(right_val) if isinstance(right_val, (str, int, float)) else right_val

                if left_num < right_num:
                    return True
            except (ValueError, TypeError):
                # Fallback para comparação de strings
                left_str = str(left_val)
                right_str = str(right_val)

                if left_str < right_str:
                    return True
        elif ' == ' in condition:
            left, right = condition.split(' == ')
            left_val = self._evaluate_expression(left)
            right_val = self._evaluate_expression(right)
            # Garantir comparação de tipos compatíveis
            try:
                # Tentar conversão numérica primeiro
                left_num = float(left_val) if isinstance(left_val, (str, int, float)) else left_val
                right_num = float(right_val) if isinstance(right_val, (str, int, float)) else right_val

                if left_num == right_num:
                    return True
            except (ValueError, TypeError):
                # Fallback para comparação de strings
                left_str = str(left_val)
                right_str = str(right_val)

                if left_str == right_str:
                    return True

        elif '.contains(' in condition:
            # Exemplo: IF input.contains('keyword'):
            match_contains = re.match(r'(.+)\.contains\((.+)\)', condition)
            if match_contains:
                container_expr = match_contains.group(1).strip()
                item_expr = match_contains.group(2).strip()
                
                container = self._evaluate_expression(container_expr)
                item = self._evaluate_expression(item_expr)

                if isinstance(container, (str, list, tuple)) and item in container:
                    return True
                # Implementação básica, pode ser expandida

        # Default para False se nenhuma condição for atendida
        return False

    def _parse_parameters(self, params_str: str) -> Dict[str, Any]:
        """Parse simples de parâmetros."""
        params = {}
        # Implementação básica
        parts = params_str.split(',')
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip()
                params[key] = self._evaluate_expression(value)
        return params

    def set_variable(self, name: str, value: Any, var_type: str = None):
        """Define uma variável HMP."""
        if var_type is None:
            var_type = type(value).__name__
        self.variables[name] = HMPVariable(name, value, var_type)

    def get_variable(self, name: str) -> Any:
        """Obtém valor de uma variável."""
        if name in self.variables:
            return self.variables[name].value
        return None

    def register_function(self, name: str, func: callable):
        """Registra uma função externa no interpretador HMP."""
        self.functions[name] = func
        logging.info(f"HMP: Função '{name}' registrada com sucesso")

    # Funções built-in específicas
    def _analyze_request(self, input: str) -> Dict[str, Any]:
        """Analisa um pedido do usuário."""
        return {
            "intent": "analysis",
            "complexity": "moderate",
            "understanding_level": 85
        }

    def _decompose_problem(self, objetivo: str, tools: List[str]) -> List[Dict]:
        """Decompõe um problema em passos."""
        return [
            {"step": 1, "action": "analyze", "tool": "analysis"},
            {"step": 2, "action": "execute", "tool": "execution"},
            {"step": 3, "action": "synthesize", "tool": "synthesis"}
        ]

    def _generate_execution_plan(self, objetivo: str, tools: List[str]) -> List[Dict]:
        """Gera plano de execução."""
        return [
            {"type": "analysis", "priority": 1},
            {"type": "execution", "priority": 2},
            {"type": "synthesis", "priority": 3}
        ]

    def _synthesize_response(self, objetivo: str, context: str) -> str:
        """Sintetiza resposta final."""
        return f"Resposta sintetizada para: {objetivo} com contexto: {context}"