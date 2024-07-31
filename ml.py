import pandas as pd
import mysql.connector
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error ,mean_squared_error , r2_score , accuracy_score
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.linear_model import LinearRegression , LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import  SVC
from sqlalchemy import create_engine

username = 'root'
password = ''
hostname = 'localhost'  # e.g., 'localhost' or '127.0.0.1'
database = 'divar2'

#create and connect to DB
conn = mysql.connector.connect(
  host=hostname,
  user=username,
  password=password,
  database=database
)
c = conn.cursor()
c.execute('''
  CREATE TABLE IF NOT EXISTS results (
      table_name TEXT,
      type TEXT,
      model TEXT,
      test_size REAL,
      standard INTEGER,
      normal INTEGER,
      dropColumns INTEGER,
      factorize INTEGER,
      dummies INTEGER,
      MAE REAL,
      RMSE REAL,
      R2 REAL,
      ACC REAL
  )
''')

#empty table before process
c.execute('DELETE FROM results')

conn.commit()

#Upload Data
query = "SELECT * FROM buyapartment"
Table = pd.read_sql_query(query,conn)

#create a dataframe for classifier models
Table_cat = Table.copy()
Table_cat['gheimate_kol'] =  Table_cat['gheimate_kol'].apply(lambda x: 'upper 500' if int(x) > 500000000 else 'lower 500')

#create a correlation matrix
corr  = pd.DataFrame.corr(Table)
corr.to_excel('corr.xlsx')

#function for show result from DB
def showResult():
  query = 'SELECT * FROM results ORDER BY table_name , type ,  R2 DESC, MAE ASC , ACC'
  connection_string = f'mysql+mysqlclient://{username}:{password}@{hostname}/{database}'
  engine = create_engine(connection_string)
  df = pd.read_sql_query(query, engine)
  df.to_excel('result.xlsx')

  engine.dispose()

def insertDB(table_name,type, model, test_size, standard,normal, dropColumns, factorize, dummies,MAE , RMSE, R2, ACC):

  insert_query = '''
    INSERT INTO results (table_name, type, model, test_size, standard,normal, dropColumns, factorize, dummies,MAE,RMSE, R2, ACC)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? , ? , ?)
  '''
  c.execute(insert_query, (table_name,type, model, test_size, standard,normal, dropColumns, factorize, dummies,MAE,RMSE, R2, ACC))

  conn.commit()


#function for prepare Data
def prepareTable(Table, standard=True, normal=False, dropColumns=False , factorize = False , dummies = False):
    #remove empty rows
    Table = Table.dropna()

    if dropColumns:
        Table = Table.drop(dropColumns, axis=1)

    numerical_cols = Table.select_dtypes(include=['number']).columns
    object_columns = Table.dtypes[Table.dtypes == 'object'].index

    if standard:
        scaler = StandardScaler()
        Table[numerical_cols] = scaler.fit_transform(Table[numerical_cols])
    elif normal:
        scaler = MinMaxScaler()
        Table[numerical_cols] = scaler.fit_transform(Table[numerical_cols])

    if factorize:
      for col in object_columns:
        Table[col], unique = pd.factorize(Table[col])
    elif dummies:
      Table = pd.get_dummies(Table, columns=object_columns, drop_first=True)

    return Table

#function Test and process data
def testTables(MainTable,ycol, test_size=0.4, selectedModel='LinearRegression',standard=True, normal=False, dropColumns=False , factorize = False , dummies = False):
    Table = prepareTable(MainTable, standard, normal, dropColumns,factorize,dummies)

    if dummies:
      x = Table.drop(Table.filter(like=ycol).columns, axis=1)
      y = Table.filter(like=ycol).iloc[:, 0]
    else:
      x = Table.drop([ycol], axis=1)
      y = Table[ycol]

    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=test_size, random_state=10)


    if selectedModel == 'LinearRegression':
      Model = LinearRegression()
    elif selectedModel == 'RandomForestRegressor':
      Model = RandomForestRegressor()
    elif selectedModel == 'LogisticRegression':
      Model = LogisticRegression()
    elif selectedModel == 'DecisionTreeClassifier':
      Model = DecisionTreeClassifier()
    elif selectedModel == 'DecisionTreeRegressor':
      Model = DecisionTreeRegressor()
    elif selectedModel == 'SVC':
      Model = SVC(random_state = 7)
    else:
        raise ValueError(f"Unsupported model type: {type}")

    Model.fit(x_train, y_train)
    y_pred_test = Model.predict(x_test)

    MAE,R2,ACC,RMSE = 'none','none','none', 'none'
    if selectedModel in ['LinearRegression','RandomForestRegressor','DecisionTreeRegressor']:
      MAE = mean_absolute_error(y_test, y_pred_test)
      RMSE = mean_squared_error(y_test, y_pred_test , squared = False)
      R2 = r2_score(y_test, y_pred_test)
      type = 'Regressor'
    else:
      ACC = accuracy_score(y_test, y_pred_test)
      type = 'Classifier'

    dropColumns_text = '_'.join(dropColumns)
    
    insertDB('boston',type,selectedModel,test_size,standard,normal,dropColumns_text,factorize,dummies,MAE,RMSE,R2,ACC)


models = ['LinearRegression','RandomForestRegressor','DecisionTreeRegressor']
test_size = [0.4,0.5]
for model in models:
  for test in test_size:   
    testTables(Table,'gheimate_kol', test, model,standard=False, normal=True, dropColumns=[],factorize = False , dummies = False)
    testTables(Table,'gheimate_kol', test, model,standard=True, normal=False, dropColumns=[],factorize = False , dummies = False)   
    testTables(Table,'gheimate_kol', test, model,standard=False, normal=True, dropColumns=[],factorize = True , dummies = False)
    testTables(Table,'gheimate_kol', test, model,standard=True, normal=False, dropColumns=[],factorize = True , dummies = False)   
    testTables(Table,'gheimate_kol', test, model,standard=False, normal=True, dropColumns=[],factorize = False , dummies = True)
    testTables(Table,'gheimate_kol', test, model,standard=True, normal=False, dropColumns=[],factorize = False , dummies = True)


models = ['LogisticRegression','DecisionTreeClassifier','SVC']
test_size = [0.4,0.5]
for model in models:
  for test in test_size:
    testTables(Table_cat,'gheimate_kol', test, model,standard=False, normal=True, dropColumns=[],factorize = True , dummies = False)
    testTables(Table_cat,'gheimate_kol', test, model,standard=True, normal=False, dropColumns=[],factorize = True , dummies = False)
    testTables(Table_cat,'gheimate_kol', test, model,standard=False, normal=True, dropColumns=[],factorize = False , dummies = True)
    testTables(Table_cat,'gheimate_kol', test, model,standard=True, normal=False, dropColumns=[],factorize = False , dummies = True)

showResult()