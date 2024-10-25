from mesa import Agent, Model
import sympy
from collections import deque
from mesa.time import SimultaneousActivation

#estructuras de datos: pila para operadores y cola para numeros
class Stack:
    def __init__(self):
        self.stack = []
    
    def push(self, item):
        self.stack.append(item)
    
    def pop(self):
        if not self.is_empty():
            return self.stack.pop()
        return None
    
    def peek(self):
        if not self.is_empty():
            return self.stack[-1]
        return None
    
    def is_empty(self):
        return len(self.stack) == 0
    
    def size(self):
        return len(self.stack)

class Queue:
    def __init__(self):
        self.queue = deque()
    
    def add(self, item):
        self.queue.append(item)
    
    def poll(self):
        if not self.is_empty():
            return self.queue.popleft()
        return None
    
    def peek(self):
        if not self.is_empty():
            return self.queue[0]
        return None
    
    def is_empty(self):
        return len(self.queue) == 0
    
    def size(self):
        return len(self.queue)

class AgenteOperacion(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.num1 = 0
        self.num2 = 0

    def set_values(self, num1, num2):
        self.num1 = num1
        self.num2 = num2

    def operacion(self):
        print(f"La operación no está definida para el agente con ID {self.unique_id}")
        return None  

    def step(self):
        return self.operacion()

class AgenteSuma(AgenteOperacion):
    def operacion(self):
        return self.num1 + self.num2

class AgenteResta(AgenteOperacion):
    def operacion(self):
        return self.num1 - self.num2

class AgenteMultiplicacion(AgenteOperacion):
    def operacion(self):
        return self.num1 * self.num2

class AgenteDivision(AgenteOperacion):
    def operacion(self):
        return self.num1 / self.num2

class AgentePotencia(AgenteOperacion):
    def operacion(self):
        return self.num1 ** self.num2

#clase token
class Token:
    def __init__(self, tipo, valor):
        self.tipo = tipo  # 'OPERADOR', 'NUMERO', 'PARENTESIS'
        self.valor = valor

    def __repr__(self):
        return f'Token({self.tipo}, {self.valor})'


class AgenteIO(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def recibir_expresion(self, expresion):
        if sympy.sympify(expresion):
            tokens = self.tokenizar_expresion(expresion)
            salida = self.shunting_yard(tokens)
            resultado = self.evaluar_postfija(salida)
            print(f"Resultado final: {resultado}")

    def tokenizar_expresion(self, expresion):
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
        precedencia = {'+': 1, '-': 1, '*': 2, '/': 2, '^': 3}
        operadores = Stack()
        salida = Queue()
        for token in tokens:
            if token.tipo == 'NUMERO':
                salida.add(token)
            elif token.tipo == 'OPERADOR':
                while not operadores.is_empty() and (precedencia.get(operadores.peek().valor, 0) >= precedencia[token.valor]):
                    salida.add(operadores.pop())
                operadores.push(token)
            elif token.valor == '(':
                operadores.push(token)
            elif token.valor == ')':
                while operadores.peek().valor != '(':
                    salida.add(operadores.pop())
                operadores.pop()
        while not operadores.is_empty():
            salida.add(operadores.pop())
        return salida

    def evaluar_postfija(self, tokens):
        pila = Stack()
        while not tokens.is_empty():
            token = tokens.poll()
            if token.tipo == 'NUMERO':
                pila.push(token.valor)
            else:
                num2 = pila.pop()
                num1 = pila.pop()
                if token.valor == '+':
                    self.model.agente_suma.set_values(num1, num2)
                    pila.push(self.model.agente_suma.step())
                elif token.valor == '-':
                    self.model.agente_resta.set_values(num1, num2)
                    pila.push(self.model.agente_resta.step())
                elif token.valor == '*':
                    self.model.agente_multiplicacion.set_values(num1, num2)
                    pila.push(self.model.agente_multiplicacion.step())
                elif token.valor == '/':
                    self.model.agente_division.set_values(num1, num2)
                    pila.push(self.model.agente_division.step())
                elif token.valor == '^':
                    self.model.agente_potencia.set_values(num1, num2)
                    pila.push(self.model.agente_potencia.step())
        return pila.pop()

class CalculadoraAgentes(Model):
    def __init__(self):
        super().__init__()
        self.schedule = SimultaneousActivation(self)

        self.agente_suma = AgenteSuma("suma", self)
        self.agente_resta = AgenteResta("resta", self)
        self.agente_multiplicacion = AgenteMultiplicacion("multiplicacion", self)
        self.agente_division = AgenteDivision("division", self)
        self.agente_potencia = AgentePotencia("potencia", self)
        self.agente_entrada_salida = AgenteIO("entrada_salida", self)

        self.schedule.add(self.agente_suma)
        self.schedule.add(self.agente_resta)
        self.schedule.add(self.agente_multiplicacion)
        self.schedule.add(self.agente_division)
        self.schedule.add(self.agente_potencia)
        self.schedule.add(self.agente_entrada_salida)


if __name__ == '__main__':
    calculadora = CalculadoraAgentes()
    expresion = "5 + ()"
    calculadora.agente_entrada_salida.recibir_expresion(expresion)
