import requests
from bs4 import BeautifulSoup
import numpy as np

VITAMINS = ['A', 'В1', 'В2', 'В3', 'В5', 'В6', 'B7', 'B9', 'B12', 'C']

FORBIDDEN_NAMES = ['тушеная', 'козий']


class Error(Exception):
    pass


class WrongPageError(Error):
    pass


class VitaminSaturation(object):
    def __init__(self, num):
        self.vitamin_dict = {}
        for vitamin in VITAMINS:
            self.vitamin_dict[vitamin] = float(num)

    def add_vitamin(self, name, value):
        self.vitamin_dict[name] += value

    def get_vitamin(self, name):
        return self.vitamin_dict[name]

    def __call__(self):
        for vitamin in VITAMINS:
            print(self.vitamin_dict[vitamin], end=' ')
        print()

    def __add__(self, other):
        cur = VitaminSaturation(0)
        for vitamin in VITAMINS:
            cur.add_vitamin(vitamin, self.vitamin_dict[vitamin])
            cur.add_vitamin(vitamin, other.vitamin_dict[vitamin])
        return cur

    def __mul__(self, other):
        cur = VitaminSaturation(0)
        for vitamin in VITAMINS:
            cur.add_vitamin(vitamin,
                            self.vitamin_dict[vitamin] * other.vitamin_dict[
                                vitamin])
        return cur

    def create_plot(self):
        return np.array(VITAMINS), np.array(list(self.vitamin_dict.values()))


class GetListOfProducts:

    def __init__(self):
        pass

    def create_url_eda5(self, page_num):
        if page_num == 1:
            return f'http://www.eda5.ru/zdorovoe_pitanie/' \
                   f'vitamins_in_food/index.html'
        else:
            return f'http://www.eda5.ru/zdorovoe_pitanie/' \
                   f'vitamins_in_food/index{page_num}.html'

    def get_response(self, page_num):
        try:
            response = requests.get(self.create_url_eda5(page_num))
            if response.status_code != 200:
                raise WrongPageError
            return response
        except WrongPageError:
            print("Wrong page selected!")
            exit(0)

    def get_dose(self, val_str):
        val_list = val_str.split('-')
        new_val_list = []
        for x in val_list:
            x = x.replace(',', '.')
            x = x.replace(' ', '')
            new_val_list.append(x)
        val_list = new_val_list
        if len(val_list) == 1:
            return float(val_list[0])
        else:
            return np.mean(list(map(float, val_list)))

    def get_dict(self):
        product_dict = {}
        for page_num in range(1, 5):
            response = self.get_response(page_num)
            soup = BeautifulSoup(response.content, 'html.parser')
            list_of_tr = soup.find_all('tr')
            list_of_tr = list_of_tr[3:]
            list_of_td_vitamins = soup.select('td[rowspan]')
            cur_vitamin = []
            cnt_of_cur_vitamin = []
            for x in list_of_td_vitamins:
                for vitamin in VITAMINS:
                    if vitamin in x.get_text():
                        cur_vitamin.append(vitamin)
                        break
                cnt_of_cur_vitamin.append(x.get('rowspan'))
            list_of_vitamins_on_page = list(
                zip(cur_vitamin, cnt_of_cur_vitamin))
            vitamin_ind = 0
            vitamin_products_cnt = \
                int(list_of_vitamins_on_page[vitamin_ind][1])
            vitamin_name = list_of_vitamins_on_page[vitamin_ind][0]
            coef = 1
            for x in list_of_tr:
                list_of_td = x.find_all('td')
                cur_text = list_of_td[0].get_text()
                if len(list_of_td) == 1 and \
                        cur_text == 'Содержание бетта-каротина:':
                    coef = 6000
                if len(list_of_td) == 2:
                    names_of_products = list_of_td[0].get_text().split(', ')
                    for name in names_of_products:
                        if name.lower() in FORBIDDEN_NAMES:
                            continue
                        if not (name.lower() in product_dict):
                            product_dict[name.lower()] = VitaminSaturation(0)
                        if vitamin_products_cnt == 0:
                            vitamin_ind += 1
                            vitamin_products_cnt = int(
                                list_of_vitamins_on_page[vitamin_ind][1])
                            vitamin_name = \
                                list_of_vitamins_on_page[vitamin_ind][0]
                        cur_dose = list_of_td[1].get_text()
                        cur_dose = self.get_dose(cur_dose) / coef
                        product_dict[name.lower()].add_vitamin(vitamin_name,
                                                               cur_dose)
                    vitamin_products_cnt -= 1
        return product_dict

    def get_normal_day_diet(self):
        norm_sat = VitaminSaturation(0)
        norm_dose_list = [800.0, 1500.0, 1200.0, 16000.0, 6000.0, 1300.0, 30.0,
                          400.0, 3.0, 80000.0]
        for id in range(len(VITAMINS)):
            norm_sat.add_vitamin(VITAMINS[id], norm_dose_list[id])
        return norm_sat
