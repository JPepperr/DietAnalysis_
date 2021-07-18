from flask import Flask, render_template, request
from ProductCollector import GetListOfProducts, VITAMINS, VitaminSaturation
import matplotlib
import matplotlib.pyplot as plt
import requests
matplotlib.use('Agg')

app = Flask(__name__)

NUMBER_OF_PRODUCTS = 10

products = GetListOfProducts()
product_list = []
products_dict = {}


@app.route("/form")
def form():
    return render_template("form.html", product_list=product_list,
                           number_of_products=NUMBER_OF_PRODUCTS)


def get_coordinates(ip_address):
    response = requests.get("http://ip-api.com/json/{}".format(ip_address))
    js = response.json()
    return js['lat'], js['lon']


@app.route("/data", methods=['GET', 'POST'])
def data():
    if request.method == 'GET':
        return f"The URL /data is accessed directly. " \
               f"Try going to '/form' to submit form"
    if request.method == 'POST':
        # ip_address = request.remote_addr
        ip_address = "78.85.5.237"
        lat, lon = get_coordinates(ip_address)
        with open('google-dev-token.txt') as token_file:
            google_token = token_file.read()
        mainpage = 'https://maps.googleapis.com/maps/api/' \
                   'place/nearbysearch/json?'
        location = str(lat) + ',' + str(lon)
        keyword = 'витамины'
        parameters = 'location=' + location + '&rankby=distance' \
                     + '&keyword=' + keyword + \
                     '&language=ru-Ru' + '&key=' + google_token
        final_url = mainpage + parameters
        response = requests.get(final_url)
        shop = {
            'vicinity': 'Not found',
            'name': 'Not found',
            'icon': 'Not found'
        }
        for shops in response.json()['results']:
            if 'store' in shops['types']:
                shop = shops
                break
        shop_link = "https://www.google.com/maps/place/?q=place_id:" + \
                    shop['place_id']

        form_data = {}
        inp_pr = []
        inp_mg = []
        un_form_data = {}
        un_inp_pr = []
        un_inp_mg = []
        for x in range(NUMBER_OF_PRODUCTS):
            cur_name = request.form["inp_pr" + str(x)]
            cur_cnt = request.form["inp_mg" + str(x)]
            if (cur_name == "" or cur_cnt == ""):
                continue
            else:
                cur_cnt = int(cur_cnt)
            if not (cur_name in products_dict):
                if cur_name in un_inp_pr:
                    cur_ind = un_inp_pr.index(cur_name)
                    un_inp_mg[cur_ind] += cur_cnt
                else:
                    un_inp_pr.append(cur_name)
                    un_inp_mg.append(cur_cnt)
            else:
                if cur_name in inp_pr:
                    cur_ind = inp_pr.index(cur_name)
                    inp_mg[cur_ind] += cur_cnt
                else:
                    inp_pr.append(cur_name)
                    inp_mg.append(cur_cnt)
        inp = list(zip(inp_pr, inp_mg))
        un_inp = list(zip(un_inp_pr, un_inp_mg))
        for x in range(len(un_inp)):
            un_form_data["inp" + str(x)] = un_inp[x]
        cur_saturation = VitaminSaturation(0)
        for x in range(len(inp)):
            form_data["inp" + str(x)] = inp[x]
            cur_saturation = cur_saturation + products_dict[
                inp[x][0]] * VitaminSaturation(float(inp[x][1]) * 10)

        plt.clf()
        x_saturation_user, y_saturation_user = cur_saturation.create_plot()
        plt.plot(x_saturation_user, y_saturation_user, label="your diet",
                 marker='o')
        x_saturation_norm, y_saturation_norm \
            = products.get_normal_day_diet().create_plot()
        plt.plot(x_saturation_norm, y_saturation_norm, label="normal diet",
                 marker='o')
        plt.fill_between(x_saturation_user, y_saturation_user,
                         y_saturation_norm,
                         where=(y_saturation_user > y_saturation_norm),
                         color='C0', alpha=0.3,
                         interpolate=True)
        plt.fill_between(x_saturation_user, y_saturation_user,
                         y_saturation_norm,
                         where=(y_saturation_user <= y_saturation_norm),
                         color='C1', alpha=0.3,
                         interpolate=True)
        plt.xlabel('Vitamins')
        plt.ylabel('Dose, mcg')
        plt.title('Vitamin diagram')
        plt.legend()
        plt.yscale('log')
        name = "gp.png"
        url = "static/" + name
        plt.savefig(url)

        return render_template("data.html", un_form_data=un_form_data,
                               form_data=form_data,
                               name=name, url=url,
                               saturation=cur_saturation,
                               norm_saturation=products.get_normal_day_diet(),
                               vitamins=VITAMINS,
                               shop_address=shop['vicinity'],
                               shop_name=shop['name'],
                               shop_id=shop_link)


if __name__ == "__main__":
    products_dict = products.get_dict()
    product_list = list(products_dict.keys())
    app.run(host="localhost", port=1234, debug=True)
