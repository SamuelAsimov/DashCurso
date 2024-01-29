import streamlit as st
import requests
import pandas as pd 
import plotly.express as px

st.set_page_config(layout='wide')

def formata_numero(valor, prefixo = ''):
    for unidade in ['', 'mil']:
        if valor < 1000:
            return f'{prefixo} {valor: .2f} {unidade}'
        valor /= 1000
    return f'{prefixo} {valor: .2f} milhões'

st.title("Curso")

url = 'https://labdados.com/produtos'
regioes = ['Brasil','Centro-Oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul']

st.sidebar.title('Filtros')
regiao=st.sidebar.selectbox('Região', regioes)

if regiao == 'Brasil':
    regiao =''

todos_anos=st.sidebar.checkbox('Dados de todo periodo', value=True)
if todos_anos:
    ano=''
else:
    ano=st.sidebar.slider('Ano', 2020, 2023)

query_string = {'regiao':regiao.lower(),'ano':ano}
response = requests.get(url, params=query_string)
dados = pd.DataFrame.from_dict(response.json())
dados['Data da Compra']=pd.to_datetime(dados['Data da Compra'], format='%d/%m/%Y')

filtro_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique())
if filtro_vendedores:
    dados=dados[dados['Vendedor'].isin(filtro_vendedores)]

### Tabelas de receita
receita_estados = dados.groupby('Local da compra')[['Preço']].sum()
receita_estados = dados.drop_duplicates(subset= 'Local da compra')[['Local da compra', 'lat', 'lon']].merge(receita_estados, left_on = 'Local da compra', right_index = True).sort_values('Preço', ascending= False)

receita_mensal=dados.set_index('Data da Compra').groupby(pd.Grouper(freq='M'))['Preço'].sum().reset_index()
receita_mensal['Ano']=receita_mensal['Data da Compra'].dt.year
receita_mensal['Mes']=receita_mensal['Data da Compra'].dt.month_name()

receita_categoria = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending = False)

#Tabelas Quantidade de vendas
vendas_estados = pd.DataFrame(dados.groupby('Local da compra')['Preço'].count())
vendas_estados = dados.drop_duplicates(subset = 'Local da compra')[['Local da compra','lat', 'lon']].merge(vendas_estados, left_on = 'Local da compra', right_index = True).sort_values('Preço', ascending = False)
vendas_estados.rename(columns={'Preço': 'Quantidade de Vendas'}, inplace=True)

vendas_mensal=dados.set_index('Data da Compra').groupby(pd.Grouper(freq='M'))['Preço'].count().reset_index()
vendas_mensal['Ano']=receita_mensal['Data da Compra'].dt.year
vendas_mensal['Mes']=receita_mensal['Data da Compra'].dt.month_name()
vendas_mensal.rename(columns={'Preço': 'Quantidade de Vendas'}, inplace=True)

vendas_categoria = dados.groupby('Categoria do Produto')[['Preço']].count().sort_values('Preço', ascending = False)
vendas_categoria.rename(columns={'Preço': 'Quantidade de Vendas'}, inplace=True)

###Tebelas vendedores
vendedores=pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum', 'count']))

## Gráficos
### Gráficos receita
fig_mapa_receita = px.scatter_geo(receita_estados,
                                  lat = 'lat',
                                  lon = 'lon',
                                  scope = 'south america',
                                  size = 'Preço',
                                  template = 'seaborn',
                                  hover_name = 'Local da compra',
                                  hover_data = {'lat': False, 'lon': False},
                                  title = 'Receita por estado')

fig_receita_mensal = px.line(receita_mensal,
                             x='Mes', 
                             y='Preço',
                             markers=True,
                             range_y=(0,receita_mensal.max()),
                             color='Ano',
                             line_dash='Ano',
                             title='Receita mensal')

fig_receita_por_estado = px.bar(receita_estados.head(),
                                y='Preço',
                                x='Local da compra',
                                title='Receita dos 5 maiores estados',
                                text_auto = True)

fig_receita_categorias=px.bar(receita_categoria,
                              text_auto = True,
                              title='Receita por categoria')

fig_receita_por_estado.update_layout(yaxis_title='Receita')
fig_receita_mensal.update_layout(yaxis_title='Receita')
fig_receita_categorias.update_layout(yaxis_title='Receita')

#Figuras quantidade de vendas
fig_mapa_vendas = px.scatter_geo(vendas_estados,
                                  lat = 'lat',
                                  lon = 'lon',
                                  scope = 'south america',
                                  size = 'Quantidade de Vendas',
                                  template = 'seaborn',
                                  hover_name = 'Local da compra',
                                  hover_data = {'lat': False, 'lon': False},
                                  title = 'Quantidade de vendas por estado')


fig_vendas_mensal = px.line(vendas_mensal,
                             x='Mes', 
                             y='Quantidade de Vendas',
                             markers=True,
                             range_y=(0,receita_mensal.max()),
                             color='Ano',
                             line_dash='Ano',
                             title='Quantidade de Vendas mensal')

fig_vendas_por_estado = px.bar(vendas_estados.head(),
                                y='Quantidade de Vendas',
                                x='Local da compra',
                                title='Vendas dos 5 maiores estados',
                                text_auto = True)

fig_vendas_categorias=px.bar(vendas_categoria,
                              text_auto = True,
                              title='Receita por categoria')




##Visualização
aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de Vendas', 'Vendedores'])

with aba1:

    col1,col2 = st.columns(2)
    with col1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_receita, use_container_witdh=True)
        st.plotly_chart(fig_receita_por_estado, use_container_width=True)
    with col2:   
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_receita_mensal, use_container_witdh=True)
        st.plotly_chart(fig_receita_categorias, use_container_width=True)

with aba2:

    col1,col2 = st.columns(2)
    with col1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_vendas, use_container_width=True)
        st.plotly_chart(fig_vendas_por_estado, use_container_width=True)
        
    with col2:   
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_vendas_mensal, use_container_witdh=True)
        st.plotly_chart(fig_vendas_categorias, use_container_width=True)
       

with aba3:
    qtd_vendedores= st.number_input('Quantidade de vendedores', 2, 10, 5)

    col1,col2 = st.columns(2)
    with col1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        fig_receita_vendedores = px.bar(vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores),
                                        x='sum',
                                        y=vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores).index,
                                        text_auto=True,
                                        title=f'Top {qtd_vendedores} vendedores (receita)')
        st.plotly_chart(fig_receita_vendedores, use_container_width=True)
    with col2:   
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        fig_vendas_vendedores = px.bar(vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores),
                                        x='count',
                                        y=vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores).index,
                                        text_auto=True,
                                        title=f'Top {qtd_vendedores} vendedores (Quantidade de vendas)')
        st.plotly_chart(fig_vendas_vendedores, use_container_width=True)
       
