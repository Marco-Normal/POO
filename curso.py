import disciplina
import unidade


class Curso:
    def __init__(self, **kwargs):
        self.nome: str = kwargs.get(nome)
        self.unidade: unidade = kwargs.get(unidade)
        self.dur_ideal: int = kwargs.get(dur_ideal)
        self.dur_min: int = kwargs.get(dur_min)
        self.dur_max: int = kwargs.get(dur_max)
        self.dis_obr: List(disciplina) = kwargs.get(dis_obr)
        self.dis_opt_livre: List(disciplina) = kwargs.get(dis_opt_livre)
        self.dis_opt_ele: List(disciplina) = kwargs.get(dis_opt_ele)
