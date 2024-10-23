from mesa import Agent, Model  # Importamos las clases base de Mesa
from mesa.time import RandomActivation  # Para activación aleatoria de agentes
import sympy  # Biblioteca para manejo de expresiones matemáticas
from collections import deque  # Para implementar colas de mensajes

# Clase para representar mensajes entre agentes
class Message:
    """
    Clase que representa un mensaje entre agentes.
    Facilita la comunicación asíncrona en el sistema.
    """
    def __init__(self, sender, receiver, content, operation_id):
        self.sender = sender          # ID del agente que envía el mensaje
        self.receiver = receiver      # ID del agente que debe recibir el mensaje
        self.content = content        # Contenido del mensaje (operación o resultado)
        self.operation_id = operation_id  # ID único para rastrear la operación

# Agente principal de Entrada/Salida
class IOAgent(Agent):
    """
    Agente que maneja la entrada de expresiones y la salida de resultados.
    Actúa como coordinador principal del sistema.
    """
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.expression = None                # Expresión matemática a procesar
        self.results = {}                     # Diccionario para almacenar resultados parciales
        self.pending_operations = deque()     # Cola de operaciones pendientes
        self.operation_counter = 0            # Contador para generar IDs únicos de operación

    def set_expression(self, expr):
        """
        Configura una nueva expresión para procesar y reinicia el estado del agente.
        """
        self.expression = expr
        self.results.clear()              # Limpia resultados anteriores
        self.pending_operations.clear()    # Limpia operaciones pendientes
        self.operation_counter = 0         # Reinicia el contador de operaciones

    def validate_expression(self):
        """
        Valida la expresión matemática usando SymPy.
        Convierte la expresión string en un objeto SymPy para su procesamiento.
        """
        try:
            self.valid_expr = sympy.sympify(self.expression)
            print(f"Expresión válida: {self.valid_expr}")
            return True
        except sympy.SympifyError:
            print(f"Expresión inválida: {self.expression}")
            return False

    def distribute_operations(self):
        """
        Analiza la expresión y distribuye las operaciones a los agentes correspondientes.
        Usa el recorrido preorder de SymPy para respetar la precedencia de operadores.
        """
        # Obtiene lista de operaciones en orden de precedencia
        operaciones = list(sympy.preorder_traversal(self.valid_expr))
        
        for op in operaciones:
            self.operation_counter += 1
            # Determina el tipo de operación y envía al agente correspondiente
            if isinstance(op, sympy.Add):
                self.model.message_queue.append(
                    Message(self.unique_id, 'suma', op, self.operation_counter)
                )
            elif isinstance(op, sympy.Mul):
                self.model.message_queue.append(
                    Message(self.unique_id, 'multiplicacion', op, self.operation_counter)
                )
            elif isinstance(op, sympy.Pow):
                self.model.message_queue.append(
                    Message(self.unique_id, 'potencia', op, self.operation_counter)
                )
            self.pending_operations.append(self.operation_counter)

    def step(self):
        """
        Método ejecutado en cada paso del modelo.
        Procesa la expresión y maneja los resultados.
        """
        # Si hay una nueva expresión, procesarla
        if self.expression and self.validate_expression():
            self.distribute_operations()
            
        # Procesar mensajes recibidos
        for msg in list(self.model.message_queue):
            if msg.receiver == self.unique_id:  # Si el mensaje es para este agente
                self.results[msg.operation_id] = msg.content  # Almacenar resultado
                self.model.message_queue.remove(msg)  # Eliminar mensaje procesado
                if msg.operation_id in self.pending_operations:
                    self.pending_operations.remove(msg.operation_id)

        # Si todas las operaciones están completadas, calcular resultado final
        if not self.pending_operations and self.results:
            final_result = sum(self.results.values())
            print(f"Resultado final: {final_result}")

# Clase base para agentes de operación
class OperationAgent(Agent):
    """
    Clase base para todos los agentes que realizan operaciones matemáticas.
    Define la estructura común y comportamiento básico.
    """
    def __init__(self, unique_id, model, operation_type):
        super().__init__(unique_id, model)
        self.operation_type = operation_type    # Tipo de operación que maneja
        self.pending_operations = {}            # Operaciones pendientes de procesar

    def process_operation(self, operation):
        """
        Procesa una operación matemática.
        Método base que debe ser implementado por las subclases.
        """
        result = operation.evalf()  # Evalúa la expresión usando SymPy
        return float(result)

    def step(self):
        """
        Procesa los mensajes pendientes en cada paso del modelo.
        """
        # Revisar mensajes en la cola
        for msg in list(self.model.message_queue):
            if msg.receiver == self.operation_type:  # Si el mensaje es para este tipo de operación
                result = self.process_operation(msg.content)  # Procesar operación
                # Enviar resultado de vuelta al IOAgent
                self.model.message_queue.append(
                    Message(self.unique_id, 1, result, msg.operation_id)
                )
                self.model.message_queue.remove(msg)  # Eliminar mensaje procesado

# Agente especializado para operaciones de potencia
class PotenciaAgent(OperationAgent):
    """
    Agente específico para manejar operaciones de potencia.
    """
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model, 'potencia')

    def process_operation(self, operation):
        """
        Procesa específicamente operaciones de potencia.
        """
        base, exp = operation.as_base_exp()  # Obtiene base y exponente
        return float(base ** exp)  # Calcula la potencia

# Modelo principal que coordina todos los agentes
class CalculadoraModel(Model):
    """
    Modelo principal que coordina la calculadora distribuida.
    Mantiene y gestiona todos los agentes y la cola de mensajes.
    """
    def __init__(self):
        super().__init__()
        self.schedule = RandomActivation(self)  # Scheduler para activación de agentes
        self.message_queue = deque()  # Cola central de mensajes
        
        # Crear instancias de todos los agentes necesarios
        self.io_agent = IOAgent(1, self)
        self.suma_agent = OperationAgent(2, self, 'suma')
        self.resta_agent = OperationAgent(3, self, 'resta')
        self.multi_agent = OperationAgent(4, self, 'multiplicacion')
        self.div_agent = OperationAgent(5, self, 'division')
        self.potencia_agent = PotenciaAgent(6, self)
        
        # Agregar todos los agentes al scheduler
        for agent in [self.io_agent, self.suma_agent, self.resta_agent, 
                     self.multi_agent, self.div_agent, self.potencia_agent]:
            self.schedule.add(agent)

    def step(self):
        """
        Ejecuta un paso del modelo, activando todos los agentes.
        """
        self.schedule.step()

# Código de ejemplo para probar el sistema
if __name__ == "__main__":
    # Crear instancia del modelo
    model = CalculadoraModel()
    
    # Lista de expresiones de prueba
    model = CalculadoraModel()
  expresion = "(2 + 3 ** (4 - 1)/0)"
  model.io_agent.set_expression(expresion)
  model.step()
