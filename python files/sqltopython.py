#this script is completely dependent on how you have your tables set up in postgresql
#here are the table names, columns,primary keys, and datatypes to use which is shown in this format:
#
#tablename, primary keys: columnname1, columnname2, etc.
#columnname:datatype,columnname:datatype,etc.
#--------------------------------------------------------------
#userinfo, primary keys: uid
#uid:text,dob:date,index:integer
#
#userinteractions, primary keys: uid,vid,date_watched
#uid:text,vid:text,date_watched:timestamp without time zone,amount_of_time_watched:smallint,vid_selected:boolean,vid_skipped:boolean,index:integer
#
#videolibrary, primary keys: vid
#vid:text,title:text,primary_category:text,sub_category:text,sub_sub_category:text,length:smallint,index:integer,release_date:timestamp without time zone

import psycopg2
import pandas as pd
from sqlalchemy import create_engine

filepath = 'filepath that AI_Data.xlsx is stored' #make sure its an .xlsx file
aidata = pd.ExcelFile('filepath//AI_Data.xlsx')
userinteractions = aidata.parse(sheet_name=2)
userinteractions['vid_selected'] = userinteractions['vid_selected'].apply(lambda x: 'True' if x==1 else 'False')
userinteractions['vid_skipped'] = userinteractions['vid_skipped'].apply(lambda x: 'True' if x==1 else 'False')
videolibrary = aidata.parse(sheet_name=1)
userinfo = aidata.parse(sheet_name=3)

dbusername = 'database username'
password = 'password'
host = '127.0.0.1'
port = '5432'
database = 'name of your local database'

engine = create_engine("postgresql+psycopg2://{user}:{pw}@localhost/{db}"
                       .format(user=dbusername,
                               pw=password,
                               db=database))

sql_query_del = 'delete from userinteractions; delete from userinfo; delete from videolibrary;'

try:
    connection = psycopg2.connect(user = dbusername,
                                  password = password,
                                  host = host,
                                  port = port,
                                  database = database)

    cursor = connection.cursor()
    cursor.execute(sql_query_del)
    connection.commit()
    
    userinfo.to_sql('userinfo', con = engine, if_exists = 'append', chunksize = 1000)
    userinteractions.to_sql('userinteractions', con = engine, if_exists = 'append', chunksize = 1000)
    videolibrary.to_sql('videolibrary', con = engine, if_exists = 'append', chunksize = 1000)


except (Exception, psycopg2.Error) as error :
    print ("Error while connecting to PostgreSQL", error)
finally:
    #closing database connection.
        if(connection):
            #cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")
