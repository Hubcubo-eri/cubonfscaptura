"""Módulo GISS: integração SOAP com o Web Service do GISS Online."""


class GISSException(Exception):
    """Erro retornado pelo Web Service GISS."""

    def __init__(self, message: str, codigo: str | None = None):
        super().__init__(message)
        self.codigo = codigo


__all__ = ["GISSException"]
