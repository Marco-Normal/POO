class Disciplina:
    def __init__(self, **kwargs):
        self.codigo: str = kwargs.get(codigo)
        self.nome: str = kwargs.get(nome)
        self.cred_aula: int = kwargs.get(cred_aula)
        self.cred_trab: int = kwargs.get(cred_aula)
        self.carga_horaria: int = kwargs.get(carga_horaria)
        self.carg_hor_est: int = kwargs.get(carg_hor_est)
        self.carg_hor_pratica: int = kwargs.get(carg_hor_pratica)
        self.atvd_teoricas: int = kwargs.get(atvd_teoricas)
