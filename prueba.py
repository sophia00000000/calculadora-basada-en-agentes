from mesa import Agent, Model
from mesa.time import RandomActivation
import sympy
from collections import deque
from mesa.time import SimultaneousActivation


class AgenteSuma(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        mensaje = self.model.obtener_mensaje(self.unique_id)
        if mensaje and mensaje.operacion == 'SUMA':
            resultado = sum(mensaje.operandos)
            self.model.enviar_resultado(self.unique_id, resultado)

class AgenteResta(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        mensaje = self.model.obtener_mensaje(self.unique_id)
        if mensaje and mensaje.operacion == 'RESTA':
            resultado = mensaje.operandos[0] - mensaje.operandos[1]
            self.model.enviar_resultado(self.unique_id, resultado)

class AgenteMultiplicacion(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        mensaje = self.model.obtener_mensaje(self.unique_id)
        if mensaje and mensaje.operacion == 'MULTIPLICACION':
            resultado = mensaje.operandos[0] * mensaje.operandos[1]
            self.model.enviar_resultado(self.unique_id, resultado)

class AgenteDivision(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        mensaje = self.model.obtener_mensaje(self.unique_id)
        if mensaje and mensaje.operacion == 'DIVISION':
            resultado = mensaje.operandos[0] / mensaje.operandos[1]
            self.model.enviar_resultado(self.unique_id, resultado)

class AgentePotencia(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        mensaje = self.model.obtener_mensaje(self.unique_id)
        if mensaje and mensaje.operacion == 'POTENCIA':
            resultado = mensaje.operandos[0] ** mensaje.operandos[1]
            self.model.enviar_resultado(self.unique_id, resultado)

#clase token
class Token:
    def __init__(self, tipo, valor):
        self.tipo = tipo  # 'OPERADOR', 'NUMERO', 'PARENTESIS'
        self.valor = valor

    def __repr__(self):
        return f'Token({self.tipo}, {self.valor})'

#clase mensaje
class Mensaje:
    def __init__(self, operacion, operandos):
        self.operacion = operacion  # Ej: 'SUMA', 'RESTA', 'MULTIPLICACION', etc.
        self.operandos = operandos  # Lista de operandos (números)

    def __repr__(self):
        return f'Mensaje({self.operacion}, {self.operandos})'

class AgenteEntradaSalida(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def recibir_expresion(self, expresion):
        #validar expresion para asi tokenizar
        if sympy.sympify(expresion):
            tokens = self.tokenizar_expresion(expresion)
            salida = self.shunting_yard(tokens)
            resultado = self.evaluar_postfija(salida)
            print(f"Resultado final: {resultado}")


    def tokenizar_expresion(self, expresion):
        # Quitar espacios y convertir la expresión en tokens (simplificado)
        tokens = []
        num = ""
        for char in expresion:
            if char.isdigit() or char == '.':
                num += char
            else:
                if num:
                    tokens.append(Token('NUMERO', float(num)))
                    num = ""
                if char in "+-*/^()":
                    tokens.append(Token('OPERADOR' if char != '(' and char != ')' else 'PARENTESIS', char))
        if num:
            tokens.append(Token('NUMERO', float(num)))
        return tokens

    def shunting_yard(self, tokens):
        #diccionario con jerarquia de operadores
        precedencia = {'+': 1, '-': 1, '*': 2, '/': 2, '^': 3}
        
        #pilas operadores y salida
        operadores = []
        salida = []
        for token in tokens:
            if token.tipo == 'NUMERO':
                salida.append(token)
            elif token.tipo == 'OPERADOR':
                while (operadores and operadores[-1].valor != '(' and precedencia.get(operadores[-1].valor, 0) >= precedencia[token.valor]):
                    salida.append(operadores.pop())
                operadores.append(token)
            elif token.valor == '(':
                operadores.append(token)
            elif token.valor == ')':
                while operadores and operadores[-1].valor != '(':
                    salida.append(operadores.pop())
                operadores.pop()
        while operadores:
            salida.append(operadores.pop())
        return salida

    def evaluar_postfija(self, tokens):
        pila = []
        for token in tokens:
            if token.tipo == 'NUMERO':
                pila.append(token.valor)
            else:
                operando2 = pila.pop()
                operando1 = pila.pop()
                if token.valor == '+':
                    mensaje = Mensaje('SUMA', [operando1, operando2])
                    pila.append(self.model.enviar_mensaje_y_esperar_resultado('suma', mensaje))
                elif token.valor == '-':
                    mensaje = Mensaje('RESTA', [operando1, operando2])
                    pila.append(self.model.enviar_mensaje_y_esperar_resultado('resta', mensaje))
                elif token.valor == '*':
                    mensaje = Mensaje('MULTIPLICACION', [operando1, operando2])
                    pila.append(self.model.enviar_mensaje_y_esperar_resultado('multiplicacion', mensaje))
                elif token.valor == '/':
                    mensaje = Mensaje('DIVISION', [operando1, operando2])
                    pila.append(self.model.enviar_mensaje_y_esperar_resultado('division', mensaje))
                elif token.valor == '^':
                    mensaje = Mensaje('POTENCIA', [operando1, operando2])
                    pila.append(self.model.enviar_mensaje_y_esperar_resultado('potencia', mensaje))
        return pila[0]

class CalculadoraAgentes(Model):
    def __init__(self):
        super().__init__()  # Llama al constructor de la clase Model
        self.schedule = SimultaneousActivation(self)

        # Crear los agentes de operación
        self.agente_suma = AgenteSuma("suma", self)
        self.agente_resta = AgenteResta("resta", self)
        self.agente_multiplicacion = AgenteMultiplicacion("multiplicacion", self)
        self.agente_division = AgenteDivision("division", self)
        self.agente_potencia = AgentePotencia("potencia", self)
        self.agente_entrada_salida = AgenteEntradaSalida("entrada_salida", self)

        # Añadir los agentes al scheduler
        self.schedule.add(self.agente_suma)
        self.schedule.add(self.agente_resta)
        self.schedule.add(self.agente_multiplicacion)
        self.schedule.add(self.agente_division)
        self.schedule.add(self.agente_potencia)
        self.schedule.add(self.agente_entrada_salida)

        # Diccionario para gestionar mensajes
        self.mensajes = {}

    def enviar_mensaje_y_esperar_resultado(self, agente_id, mensaje):
        self.mensajes[agente_id] = mensaje
        self.schedule.step()  # Simular un paso
        return self.mensajes.get(f"resultado_{agente_id}")

    def obtener_mensaje(self, agente_id):
        return self.mensajes.pop(agente_id, None)

    def enviar_resultado(self, agente_id, resultado):
        self.mensajes[f"resultado_{agente_id}"] = resultado

if __name__ == '__main__':
    calculadora = CalculadoraAgentes()
    expresion = "(2*(3 * 44) - 5) ^ ((4+3-1)*2)"
    calculadora.agente_entrada_salida.recibir_expresion(expresion)
