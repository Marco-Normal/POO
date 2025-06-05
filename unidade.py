import curso


class Unidade:
    def __init__(self, nome: str):
        self.cursos: List(curso) = []
        self.nome: str = self.nome

    def adicionarCurso(self, novo: curso):
        self.cursos.append(novo)
