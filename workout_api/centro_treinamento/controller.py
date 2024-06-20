from uuid import uuid4
from pydantic import UUID4
from fastapi import APIRouter, Body, status, HTTPException
from workout_api.contrib.dependencies import DatabaseDependency
from workout_api.centro_treinamento.schemas import CentroTreinamentoIn, CentroTreinamentoOut
from workout_api.centro_treinamento.models import CentroTreinamentoModel
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

router = APIRouter()

@router.post(
    '/',
    summary='Cria um novo centro de treinamento',
    status_code=status.HTTP_201_CREATED,
    response_model=CentroTreinamentoOut,
)
async def post(
  db_session: DatabaseDependency,
  centro_treinamento_in: CentroTreinamentoIn = Body(...)
) -> CentroTreinamentoOut:
  try:
    centro_treinamento_out = CentroTreinamentoOut(id=uuid4(), **centro_treinamento_in.model_dump())
    centro_treinamento_model = CentroTreinamentoModel(**centro_treinamento_out.model_dump())
    db_session.add(centro_treinamento_model)
    await db_session.commit()
  except IntegrityError as err:
    raise HTTPException(
      status_code=status.HTTP_303_SEE_OTHER,
      detail=f'Já existe um centro de treinamento cadastrado com o nome {centro_treinamento_in.nome}'
    )
  except Exception as err:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=err
    )
  return centro_treinamento_out

@router.get(
    '/',
    summary='Consultar todos os centros de treinamento',
    status_code=status.HTTP_200_OK,
    response_model=list[CentroTreinamentoOut],
)
async def query(
  db_session: DatabaseDependency,
) -> list[CentroTreinamentoOut]:
  centro_treinamentos: list[CentroTreinamentoOut] = (await db_session.execute(
    select(CentroTreinamentoModel)
  )).scalars().all()
  return centro_treinamentos

@router.get(
    '/{id}',
    summary='Consultar um centro de treinamento por ID',
    status_code=status.HTTP_200_OK,
    response_model=CentroTreinamentoOut,
)
async def query(
  id: UUID4,
  db_session: DatabaseDependency,
) -> CentroTreinamentoOut:
  centro_treinamento: CentroTreinamentoOut = (await db_session.execute(
    select(CentroTreinamentoModel).filter_by(id=id)
  )).scalars().first()
  if not centro_treinamento:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail=f'Centro de treinamento não encontrado no ID {id}'
    )
  return centro_treinamento