from uuid import uuid4
from pydantic import UUID4
from fastapi import APIRouter, Body, status, HTTPException
from workout_api.contrib.dependencies import DatabaseDependency
from workout_api.categorias.schemas import CategoriaIn, CategoriaOut
from workout_api.categorias.models import CategoriaModel
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from fastapi_pagination import LimitOffsetPage
from fastapi_pagination.ext.sqlalchemy import paginate

router = APIRouter()

@router.post(
    '/',
    summary='Cria uma nova categoria',
    status_code=status.HTTP_201_CREATED,
    response_model=CategoriaOut,
)
async def post(
  db_session: DatabaseDependency,
  categoria_in: CategoriaIn = Body(...)
) -> CategoriaOut:
  try:
    categoria_out = CategoriaOut(id=uuid4(), **categoria_in.model_dump())
    categoria_model = CategoriaModel(**categoria_out.model_dump())
    db_session.add(categoria_model)
    await db_session.commit()
  except IntegrityError as err:
    raise HTTPException(
      status_code=status.HTTP_303_SEE_OTHER,
      detail=f'Já existe uma categoria cadastrada com o nome {categoria_in.nome}'
    )
  except Exception as err:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=err
    )
  return categoria_out

@router.get(
    '/',
    summary='Consultar todas as categorias',
    status_code=status.HTTP_200_OK,
    response_model=list[CategoriaOut],
)
async def query(
  db_session: DatabaseDependency,
) -> list[CategoriaOut]:
  categorias: list[CategoriaOut] = (await db_session.execute(
    select(CategoriaModel)
  )).scalars().all()
  return categorias

@router.get(
    '/getAllWithPagination',
    summary='Consultar todas as categorias (com paginação)',
    status_code=status.HTTP_200_OK,
    response_model=LimitOffsetPage[CategoriaOut],
)
async def query(
  db_session: DatabaseDependency,
) -> LimitOffsetPage[CategoriaOut]:
  try:
    categorias = await paginate(db_session, select(CategoriaModel))
  except Exception as err:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Ocorreu um erro: {err}"
    )
  return categorias

@router.get(
    '/{id}',
    summary='Consultar uma categoria por ID',
    status_code=status.HTTP_200_OK,
    response_model=CategoriaOut,
)
async def query(
  id: UUID4,
  db_session: DatabaseDependency,
) -> CategoriaOut:
  categoria: CategoriaOut = (await db_session.execute(
    select(CategoriaModel).filter_by(id=id)
  )).scalars().first()
  if not categoria:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail=f'Categoria não encontrada no ID {id}'
    )
  return categoria