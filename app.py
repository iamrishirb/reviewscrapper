from flask import Flask, render_template, request
from bs4 import BeautifulSoup as bs
import requests 
import pymongo 

app = Flask(__name__)

# Global Varibles 
base_url = "https://flipkart.com"
dbConn = pymongo.MongoClient("mongodb+srv://mongodbuser:mongodbpassword@cluster0-lsptd.mongodb.net/test?retryWrites=true&w=majority")
db_name = "flipkart"
db = dbConn[db_name]

# dic = {
#      "title" : [],
#      "review" : [],
#      "user_name" : []
# }

# Extract ten reviews for each product name ten pages max 
def extract_reviews(reviews_link, page_length, search_string) :
    
    if( page_length == 0 ):
        return
    
    # Make the connection to collection
    search_string_col_name = db[search_string]
    

    u_client = requests.get(reviews_link)
    soup = bs(u_client.content, "html.parser")
    
    # First page Reviews extract and store the reviews in the dbs 
    mydivs = soup.findAll("div", {"class": "_1gY8H-"})
    for one_box in mydivs :
        title = one_box.div.p.get_text()
        review = one_box.find(class_ = "").get_text()
        user_name = one_box.find(class_ = "_3sxSiS").get_text()

        # create a document and insert into collections
        document = {"title" : title, "review" : review, "user_name" : user_name}
        search_string_col_name.insert_one(document)
        
    next_review_link = ""    
    # where next and page button is present
    list_length = len(soup.find_all("a", {"class" : "_3fVaIS"}))
    
    if(list_length == 1) :
        route_url = soup.find_all("a", {"class" : "_3fVaIS"})[0]['href']
#         print(route_url)
#         print(type(route_url))
#         route_url = soup.find_all("a", {"class" : "_3fVaIS"})['href']
        next_review_link = base_url + route_url
        print(next_review_link)
        
    elif(list_length == 2):
        route_url = soup.find_all("a", {"class" : "_3fVaIS"})[1]['href']
        next_review_link = base_url + route_url
        print(next_review_link)
        
    return extract_reviews(next_review_link, page_length-1, search_string)

def review_url(first_box_url, search_string) :
    
    u_client = requests.get(first_box_url)
    soup = bs(u_client.content, "html.parser")
    review_link_div = soup.find("div", {"class" : "swINJg"})
    reviews_link = base_url + review_link_div.find_parent()['href'] # Actually review link to extract the information
    print(reviews_link, search_string)
    extract_reviews(reviews_link, 10, search_string)

def search_first_box_url(url, search_string) :
    
    u_client = requests.get(url)
    soup = bs(u_client.content, "html.parser")
    first_box_url = base_url + soup.find(class_ = "_31qSD5")['href'] # first box url links
    print(first_box_url)
    review_url(first_box_url, search_string)



# search product name then we have to create the collections

@app.route("/", methods = ["GET", "POST"])
def home() :
    if request.method == "POST" :
        search_string = request.form['searchString'] # need to make a collections name = search_string
        search_string = search_string.replace(" ", "") 

        reviews = db[search_string].find({}) # return the cursor objects take all the reviews
        if db[search_string].count_documents({}) > 0 :   # return the results
            return render_template("result.html", reviews = reviews)

        else : # Crawl from the sites
            url = base_url + "/search?q=" + str(search_string)
            search_first_box_url(url, search_string)
            reviews = db[search_string].find({})
            return render_template('result.html', reviews = reviews)
    return render_template("index.html")

@app.route('/test') 
def test() :
    return render_template("test.html")

if __name__ == "__main__":
    app.run(debug = True)
