from  sklearn import tree
import mysql.connector

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="divar"
)
mycursor = mydb.cursor()

sql_where = "SELECT * FROM rentapartment"
mycursor.execute(sql_where)
rows = mycursor.fetchall()

x = []
y = []

for row in rows:
    x.append(row[3:11])
    y.append(row[11:13])

clf = tree.DecisionTreeClassifier()
clf = clf.fit(x , y)

metraj = input('metraj')
sale_sakht = input('sale_sakht')
otagh = input('Otagh:')
asansor = input('asansore 0 or 1:')
anbari = input('anbari 0 or 1:')
parking = input('parking 0 or 1:')
tabaghe = input('tabaghe')
kolle_tabaghat = input('kolle tabaghat:')
new_data = [[metraj, sale_sakht  , otagh , asansor , anbari , parking , tabaghe , kolle_tabaghat]]
answer = clf.predict(new_data)
print(answer[0])
