from mesa import Agent, Model
import sympy
from collections import deque
from mesa.time import SimultaneousActivation

#estructuras de datos: pila para operadores y cola para numeros
class Stack:
    def __init__(self):
        self.stack = []
    
    def push(self, dato):
        self.stack.append(dato)
    
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
    
    def add(self, dato):
        self.queue.append(dato)
    
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

#cada agente necesita un id único
class AgenteOperacion(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.num1 = 0
        self.num2 = 0

    def set_num(self, num1, num2):
        self.num1 = num1
        self.num2 = num2

    def operacion(self):
        print(f"La operación no está definida para el agente con ID {self.unique_id}")
        return None  

    def step(self):
        return self.operacion()

class AgenteSuma(AgenteOperacion):
    def operacion(self):
        #en caso de sumar con cero:
        if self.num1 == 0:
            return self.num2
        if self.num2 == 0:
            return self.num1
        #suma normal:
        return self.num1 + self.num2

class AgenteResta(AgenteOperacion):
    def operacion(self):
        # caso de resta con cero
        if self.num2 == 0:
            return self.num1
        return self.num1 - self.num2

class AgenteMultiplicacion(AgenteOperacion):
    def operacion(self):
        # caso de multiplicación por cero
        if self.num1 == 0 or self.num2 == 0:
            return 0
        return self.num1 * self.num2

class AgenteDivision(AgenteOperacion):
    def operacion(self):
        # caso  división por cero
        if self.num2 == 0:
            raise ZeroDivisionError("División por cero no permitida")
        #caso numerador cero
        if self.num1 == 0:
            return 0
        #caso normal
        return self.num1 / self.num2

class AgentePotencia(AgenteOperacion):
    def operacion(self):
        if self.num2 == 0:
            return 1
        if self.num1 == 0:
            return 0
        return self.num1 ** self.num2


#clase token
class Token:
    def __init__(self, tipo, valor):
        self.tipo = tipo  # OPERADOR, NUMERO o 'PARENTESIS'
        self.valor = valor

    def __repr__(self):
        return f'Token({self.tipo}, {self.valor})'


class AgenteIO(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def ingresar_expresion(self, expresion):
        #si valida la expresion
        try:
            expresion_valida = sympy.sympify(expresion)
            # Aquí imprimimos para debug si la expresión es válida
            print(f"\nExpresión '{expresion}' validada: {expresion_valida}")
            tokens = self.tokenizar_expresion(expresion)
            print(tokens)
            salida = self.shunting_yard(tokens)
            # Imprime cada token en la cola de salida
            print("Tokens en notación postfija:")
            for token in list(salida.queue):
                print(token , end= " ")

            resultado = self.procesar_postfija(salida)
            if resultado is not None:
                print(f"Resultado: {resultado}")
            else:
                print("Resultado no calculado correctamente o es None.")
        except Exception as e:
            print(f"\nError !!: {str(e)}")

    def tokenizar_expresion(self, expresion):
        #lista de objetos de tipo token
        tokens = []
        # en caso de un numero de mas de una cifra o decimal
        num = ""
        for char in expresion:
            if char.isdigit() or char == '.':
                num += char
            else:   
                if len(num)!=0:
                    tokens.append(Token('NUMERO', float(num)))
                    ##vaciar numero para el siguiente
                    num = ""
                if char in "()":
                    tokens.append(Token('PARENTESIS', char))
                if char in "+-*/^":
                    tokens.append(Token('OPERADOR', char))
        if len(num)!=0:
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

    def procesar_postfija(self, tokens):
        print("procesando...")
        pila = Stack()
        while not tokens.is_empty():
            token = tokens.poll()
            if token.tipo == 'NUMERO':
                pila.push(token.valor)
            else:
                num2 = pila.pop()
                num1 = pila.pop()
                if token.valor == '+':
                    self.model.agente_suma.set_num(num1, num2)
                    pila.push(self.model.agente_suma.step())
                elif token.valor == '-':
                    self.model.agente_resta.set_num(num1, num2)
                    pila.push(self.model.agente_resta.step())
                elif token.valor == '*':
                    self.model.agente_multiplicacion.set_num(num1, num2)
                    pila.push(self.model.agente_multiplicacion.step())
                elif token.valor == '/':
                    self.model.agente_division.set_num(num1, num2)
                    pila.push(self.model.agente_division.step())
                elif token.valor == '^':
                    self.model.agente_potencia.set_num(num1, num2)
                    pila.push(self.model.agente_potencia.step())
        resultado_final = pila.pop()
        return resultado_final

class CalculadoraAgentes(Model):
    def __init__(self):
        super().__init__()
        self.schedule = SimultaneousActivation(self)

        self.agente_suma = AgenteSuma("suma", self)
        self.agente_resta = AgenteResta("resta", self)
        self.agente_multiplicacion = AgenteMultiplicacion("multiplicacion", self)
        self.agente_division = AgenteDivision("division", self)
        self.agente_potencia = AgentePotencia("potencia", self)
        self.agenteIO = AgenteIO("entrada_salida", self)

        self.schedule.add(self.agente_suma)
        self.schedule.add(self.agente_resta)
        self.schedule.add(self.agente_multiplicacion)
        self.schedule.add(self.agente_division)
        self.schedule.add(self.agente_potencia)
        self.schedule.add(self.agenteIO)


if __name__ == '__main__':
    calculadora = CalculadoraAgentes()
    expresion = "7^0"
    calculadora.agenteIO.ingresar_expresion(expresion)
