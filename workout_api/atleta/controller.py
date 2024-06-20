from datetime import datetime
from pydantic import UUID4
from fastapi import APIRouter, Body, status, HTTPException, Query
from workout_api.contrib.dependencies import DatabaseDependency
from workout_api.atleta.schemas import AtletaIn, AtletaOut, AtletaUpdate, AtletaSimplified
from workout_api.atleta.models import AtletaModel
from workout_api.categorias.models import CategoriaModel
from workout_api.centro_treinamento.models import CentroTreinamentoModel
from uuid import uuid4
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

router = APIRouter()
          
@router.post(
    '/',
    summary='Criar um novo atleta',
    status_code=status.HTTP_201_CREATED,
    response_model=AtletaOut, 
)
async def post(
  db_session: DatabaseDependency,
  atleta_in: AtletaIn = Body(...)
):
  categoria = (await db_session.execute(
    select(CategoriaModel).filter_by(nome=atleta_in.categoria.nome)
  )).scalars().first()
  if not categoria:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail=f'A categoria {atleta_in.categoria.nome} não foi encontrada',
    )
  
  centro_treinamento = (await db_session.execute(
    select(CentroTreinamentoModel).filter_by(nome=atleta_in.centro_treinamento.nome)
  )).scalars().first()
  if not centro_treinamento:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail=f'O centro de treinamento {atleta_in.centro_treinamento.nome} não foi encontrado',
    )
  try:
    atleta_out = AtletaOut(id=uuid4(), created_at=datetime.now(), **atleta_in.model_dump())
    atleta_model = AtletaModel(**atleta_out.model_dump(exclude={'categoria', 'centro_treinamento'}))
    atleta_model.categoria_id = categoria.pk_id
    atleta_model.centro_treinamento_id = centro_treinamento.pk_id
    db_session.add(atleta_model)
    await db_session.commit()
  except IntegrityError as err:
    raise HTTPException(
      status_code=status.HTTP_303_SEE_OTHER,
      detail=f'Já existe um atleta cadastrado com o CPF {atleta_in.cpf}'
    )
  except Exception as err:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=err
    )
  return atleta_out

@router.get(
    '/',
    summary='Consultar todos os atletas',
    status_code=status.HTTP_200_OK,
    response_model=list[AtletaOut],
)
async def query(
  db_session: DatabaseDependency,
) -> list[AtletaOut]:
  atletas: list[AtletaOut] = (await db_session.execute(
    select(AtletaModel)
  )).scalars().all()
  return [atleta for atleta in atletas]

@router.get(
    '/getAllSimplified/',
    summary='Consultar todos os atletas (simplificado)',
    status_code=status.HTTP_200_OK,
    response_model=list[AtletaSimplified],
)
async def query(
  db_session: DatabaseDependency,
) -> list[AtletaSimplified]:
  atletas: list[AtletaSimplified] = (await db_session.execute(
    select(AtletaModel)
  )).scalars().all()
  return [atleta for atleta in atletas]

@router.get(
    '/{id}',
    summary='Consultar um atleta por ID',
    status_code=status.HTTP_200_OK,
    response_model=AtletaOut,
)
async def query(
  id: UUID4,
  db_session: DatabaseDependency,
) -> AtletaOut:
  atleta: AtletaOut = (await db_session.execute(
    select(AtletaModel).filter_by(id=id)
  )).scalars().first()
  if not atleta:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail=f'Atleta não encontrado no ID {id}'
    )
  return atleta

@router.get(
    '/findByName/{nome}',
    summary='Consultar um atleta por nome',
    status_code=status.HTTP_200_OK,
    response_model=AtletaOut,
)
async def query(
  nome: str,
  db_session: DatabaseDependency,
) -> AtletaOut:
  atleta: AtletaOut = (await db_session.execute(
    select(AtletaModel).filter_by(nome=nome)
  )).scalars().first()
  if not atleta:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail=f'Atleta não encontrado no nome {nome}'
    )
  return atleta

@router.get(
    '/findByCPF/{cpf}',
    summary='Consultar um atleta por CPF',
    status_code=status.HTTP_200_OK,
    response_model=AtletaOut,
)
async def query(
  cpf: str,
  db_session: DatabaseDependency,
) -> AtletaOut:
  atleta: AtletaOut = (await db_session.execute(
    select(AtletaModel).filter_by(cpf=cpf)
  )).scalars().first()
  if not atleta:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail=f'Atleta não encontrado no CPF {cpf}'
    )
  return atleta

@router.patch(
    '/{id}',
    summary='Editar um atleta por ID',
    status_code=status.HTTP_200_OK,
    response_model=AtletaOut,
)
async def query(
  id: UUID4,
  db_session: DatabaseDependency,
  atleta_up: AtletaUpdate = Body(...)
) -> AtletaOut:
  atleta: AtletaOut = (await db_session.execute(
    select(AtletaModel).filter_by(id=id)
  )).scalars().first()
  if not atleta:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail=f'Atleta não encontrado no ID {id}'
    )
  try:
    atleta_update = atleta_up.model_dump(exclude_unset=True)
    for key, value in atleta_update.items():
      setattr(atleta, key, value)
    await db_session.commit()
    await db_session.refresh(atleta)
  except IntegrityError as err:
    raise HTTPException(
      status_code=status.HTTP_303_SEE_OTHER,
      detail=f'Ocorreu um erro de integridade: {err}'
    )
  except Exception as err:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=err
    )
  return atleta

@router.delete(
    '/{id}',
    summary='Deletar um atleta por ID',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def query(
  id: UUID4,
  db_session: DatabaseDependency,
) -> None:
  try:
    atleta: AtletaOut = (await db_session.execute(
      select(AtletaModel).filter_by(id=id)
    )).scalars().first()
    if not atleta:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f'Atleta não encontrado no ID {id}'
      )
    await db_session.delete(atleta)
    await db_session.commit()
  except IntegrityError as err:
    raise HTTPException(
      status_code=status.HTTP_303_SEE_OTHER,
      detail=f'Ocorreu um erro de integridade: {err}'
    )
  except Exception as err:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=err
    )