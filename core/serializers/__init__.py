from .autor import AutorSerializer
from .categoria import CategoriaSerializer
from .compra import CompraSerializer
from .compra import(
    CompraCreateUpdateSerializer,
    ItensCompraCreateUpdateSerializer,
    CompraSerializer,
    ItensCompraSerializer,
    CompraListSerializer,
    ItensCompraListSerializer,
)

from .editora import EditoraSerializer
from .livro import LivroListSerializer, LivroRetrieveSerializer, LivroSerializer
from .user import UserRegistrationSerializer, UserSerializer
