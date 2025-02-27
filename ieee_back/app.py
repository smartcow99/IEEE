import json
from urllib import response
from flask import Flask, request, jsonify

response = ""

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

@app.route('/')
def home() :
  return "hello flask!"

@app.route('/monthly', methods = ['GET', 'POST'])
def monthlyRoute() :
  
  global response
  
  if(request.method == 'POST') :
    request_data = request.data
    request_data = json.loads(request_data.decode('utf-8'))
    
    def monthly():
      import pandas as pd
      pd.set_option('mode.chained_assignment', None)
      
      # 데이터 적재
      borrowed_book = pd.read_csv('./데이터_단행본대출.csv', encoding='cp949', low_memory=False)
      lib_book = pd.read_csv('./데이터_단행본도서.csv', encoding='cp949', low_memory=False)
      
      # 불필요한 테이블(열) 삭제
      borrowed_book.drop(columns=['반납일시', '등록번호', '연대출권수'], inplace=True)
      lib_book.drop(columns=['등록번호', '등록일자', '수서구분', 'BIBLIO_ID'], inplace=True)
      renewed_book = borrowed_book[(borrowed_book['대출연장구분'] == '연장')].index
      borrowed_book.drop(renewed_book, inplace=True)
      
      
      # 단행본 대출 데이터 결측치 확인 및 제거
      borrowed_book.dropna(subset=['ISBN'], inplace=True)
      borrowed_book.dropna(subset=['상위소속'], inplace=True)
      
      
      # 단행본 도서 데이터 결측치 확인 및 제거 => fillna()을 사용해 missing으로 채우기
      lib_book.fillna('missing', inplace=True)
      
      # borrowed_book에 'rating' 열 추가 및 전부 1로 초기화
      # rating 수치는 대출수이며, 뒤에 유클리디언 유사도에서 사용함
      borrowed_book['rating'] = 1
      borrowed_book.drop(columns=['대출연장구분', '입학년도', '소속', '상위소속'], inplace=True)
      # year = request_data["yearly"]
      # month = request_data["monthly"]
      year = "2018"
      month = "02"
      borrowed_book['대출일시'] = (borrowed_book.대출일시.str.split('/').str[0] == year) & (borrowed_book.대출일시.str.split('/').str[1] == month)
      # print(borrowed_book.head())
      false_year = borrowed_book[(borrowed_book['대출일시'] == False)].index
      borrowed_book.drop(false_year, inplace=True)
      
      from collections import Counter
      
      # rating 값을 같은 이름을 가진 책의 갯수를 세어서 대치함
      for i in borrowed_book.index:
          tmp = Counter(borrowed_book['서명'])[borrowed_book.loc[i,'서명']]
          borrowed_book['rating'][i] = tmp
      
      # ISBN으로 중복 데이터를 drop 시킬려 했으나
      # 다른 책인데 동일 ISBN을 갖고 있는 데이터가 있어서
      # 서명으로 중복 데이터를 제거함
      borrowed_book.drop_duplicates(['서명'], keep='first', inplace = True)
      ranking_book = borrowed_book.sort_values(by=['rating'], ascending=False).head(10)
      # print(borrowed_book.info())
      ranking_book.reset_index(inplace=True)
      ranking_book.drop(columns='index', inplace=True)
      print(ranking_book.head(10))
      info_book_df = pd.DataFrame()
      
      
      for i in range(0,10):
          con = lib_book.ISBN == ranking_book.loc[i].ISBN
          info_book_df = pd.concat([info_book_df, lib_book[con].iloc[:1]])
      
      info_book_df.reset_index(inplace=True)
      info_book_df.drop(columns='index', inplace=True)
      
      info_book_dict = info_book_df.to_dict('records')
      print(info_book_dict)
      return info_book_dict
      
    result = monthly()
    
    response = result
    return jsonify(response)
  else :
    return jsonify(response)
    
  


@app.route('/recommend', methods = ['GET', 'POST'])
def userRoute() :
  
  global response
  
  if(request.method == 'POST') :
    request_data = request.data
    request_data = json.loads(request_data.decode('utf-8'))

    def recommend():
      import pandas as pd
      
      pd.set_option('mode.chained_assignment', None)
      pd.set_option('display.max_rows', 600)
      pd.set_option('display.max_columns', 100)
      pd.set_option('display.width', 1000)

      # 데이터 적재
      borrowed_book = pd.read_csv('./데이터_단행본대출.csv', encoding='cp949', low_memory=False)
      lib_book = pd.read_csv('./데이터_단행본도서.csv', encoding='cp949', low_memory=False)

      # 불필요한 테이블(열) 삭제
      borrowed_book.drop(columns=['대출일시', '반납일시', '등록번호', '연대출권수'], inplace=True)
      lib_book.drop(columns=['등록번호', '등록일자', '수서구분', 'BIBLIO_ID'], inplace=True)
      renewed_book = borrowed_book[(borrowed_book['대출연장구분'] == '연장')].index
      borrowed_book.drop(renewed_book, inplace=True)

      # 단행본 대출 데이터 결측치 확인 및 제거
      borrowed_book.dropna(subset=['ISBN'], inplace=True)
      borrowed_book.dropna(subset=['상위소속'], inplace=True)


      # 단행본 도서 데이터 결측치 확인 및 제거 => fillna()을 사용해 missing으로 채우기
      lib_book.fillna('missing', inplace=True)


      # borrowed_book에 'rating' 열 추가 및 전부 1로 초기화
      # rating 수치는 대출수이며, 뒤에 유클리디언 유사도에서 사용함
      borrowed_book['rating'] = 1

      '''
      사용자로부터 단과대, 학과, 입학년도를 입력받음
      입력값을 기준으로 도서를 추천해줌
      '''
      college = request_data["college"]
      department = request_data["major"]
      student_ID = int(request_data["year"])

      '''
      입력값을 기준으로 피봇팅
      '''
      u_college = borrowed_book['상위소속'] == college
      u_department = borrowed_book['소속'] == department
      u_student_ID = borrowed_book['입학년도'] == student_ID
      u_borrowed_book = borrowed_book[u_college & u_department & u_student_ID]

      from collections import Counter

      # rating 값을 같은 이름을 가진 책의 갯수를 세어서 대치함
      for i in u_borrowed_book.index:
          tmp = Counter(u_borrowed_book['서명'])[u_borrowed_book.loc[i,'서명']]
          u_borrowed_book['rating'][i] = tmp

      u_borrowed_book.drop_duplicates(['서명'], keep='first', inplace = True)

      '''
      사용자의 도서 정보가 없기 때문에,
      임의의 책을 데이터로 넣어서 추천해줌.
      임의의 책은 상위 rating 5개를 추출해서 무작위로 선정
      '''
      u_borrowed_book= u_borrowed_book.sort_values('rating', ascending=False)
      random_book = u_borrowed_book.iloc[:5]
      random_book = random_book.sample(n=1)

      '''
      아이템 기반 추천 알고리즘에서 사용하기 위한 테이블 작성
      열은 책 제목, index는 입학년도로 하여 rating을 피봇팅함.
      '''
      book_user_rating = u_borrowed_book.pivot_table('rating', index = '입학년도', columns='서명')
      book_user_rating_T = book_user_rating.transpose()



      from sklearn.metrics.pairwise import euclidean_distances

      '''
      유클리드 유사도는 rating을 벡터값으로 표현하여
      두 지점간 거리 계산, 유사도를 측정한다.
      코사인 유사도는 벡터의 방향성을 계산하여 유사도를 측정하는데,
      rating은 대출횟수이므로 방향성보다는 거리 측정이 더 알맞다 판단하여 유클리드 유사도를 사용
      '''
      euclidean_distances(book_user_rating_T, book_user_rating_T)
      euclidean_similarty = 1 / (euclidean_distances(book_user_rating_T, book_user_rating_T) +1e-5)
      similarity_rate_df = pd.DataFrame(euclidean_similarty, index = book_user_rating.columns, columns= book_user_rating.columns)
      recommand_book = similarity_rate_df[random_book['서명'].values[0]].sort_values(ascending=True)[:4]

      '''
      추천된 책을 단행본 도서.csv 파일과 연동하여
      도서 정보 출력
      '''
      recommand_book_df = pd.Series.to_frame(self=recommand_book, name='rating')
      recommand_book_df_T = recommand_book_df.transpose()
      info_book_df=pd.DataFrame()
      for i in range(0, 3):
          con = u_borrowed_book.서명 == recommand_book_df_T.columns[i]
          con_ISBN = lib_book.ISBN == u_borrowed_book[con].ISBN.values[0]
          info_book_df = pd.concat([info_book_df, lib_book[con_ISBN].iloc[:1]])

      info_book_df.reset_index(inplace=True)
      info_book_df.drop(columns='index', inplace=True)
      info_book_dict = info_book_df.to_dict('records')
      print(info_book_dict)

      return info_book_dict
    result = recommend()
    
    response = result
    return jsonify(response)
  else :
    return jsonify(response)
