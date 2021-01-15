import pandas as pd
import re
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


chrome_driver = r'C:\Users\Hovak\Desktop\study\pythonProject\chromedriver.exe'

MODELS = {}
TRIMS = {}
EACH_ROW = []
# '현대':'303','제네시스':'304',  아래 브랜드에서 일단 현대 제외함
BRANDS = [
    {'국산': {'현대': '303', '제네시스': '304', '기아': '307', '쉐보레': '312', '쌍용': '326', '르노삼성': '321'}},
    {'수입': {'BMW': '362', '벤츠': '349', '아우디': '371', '폭스바겐': '376', '푸조': '413', '시트로앵': '422', 'DS': '618', '미니': '367',
            '볼보': '459', '재규어': '394', '랜드로버': '399', '포르쉐': '381', '람보르기니': '440', '페라리': '436', '마세라티': '445', '피아트': '427',
            '애스턴마틴': '404', '맥라렌': '409', '벤틀리': '390', '롤스로이스': '385', '토요타': '491', '렉서스': '486', '혼다': '500',
            '포드': '569', '링컨': '573', '캐딜락': '546', '지프': '587', '테슬라': '611'}}
]
PRICETYPE = [1, 2, 3]
PERIOD = [36, 48, 60]
PRODTYPE = ['R', 'L']


def get_model_info(brandcode):
    brand_url = 'http://auto.danawa.com/auto/?Work=brand&Brand={brandcode}'.format(brandcode=brandcode)
    driver = webdriver.Chrome(chrome_driver)
    driver.get(brand_url)
    src = driver.page_source
    soup = BeautifulSoup(src)
    driver.close()

    # 특정 브랜드의 판매중인 모든 차량의 모델 코드, 모델 명칭을 가져옴
    sale_cars = soup.select(
        '#autodanawa_gridC > div.gridMain > article > main > div.brandModel.newcar > dl > dd > ul > li')

    return sale_cars


def get_model_trims(modelcode):
    model_url = 'http://auto.danawa.com/auto/?Work=model&Model={modelcode}'
    driver = webdriver.Chrome(chrome_driver)
    driver.get(model_url.format(modelcode=modelcode))
    src = driver.page_source
    soup = BeautifulSoup(src)
    driver.close()

    model_trim_list = soup.select('#autodanawa_gridC > div.gridMain > article > main > div.modelSection.container_modelprice > div.price_contents.on')

    return model_trim_list


def get_target_prices(is_imported, brand_key, brand_val, model_code, trimcode, prodtype, period, pricetype):
    compare_url = 'http://auto.danawa.com/leaserent/?Work=priceCompare&Model={modelcode}&Trims={trimcode}&ProdType={prodtype}&Period={period}&PriceType={pricetype}'
    target_url = compare_url.format(modelcode=model_code, trimcode=trimcode, prodtype=prodtype, period=period,
                                    pricetype=pricetype)
    driver.get(target_url)

    if target_url == driver.current_url:
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR,
                                                                        '#rentLeaserResult > div.re_call > div.reh_con_list')))

        src1 = driver.page_source
        soup = BeautifulSoup(src1)

        is_problem = ''
        price_compare_list = []
        price_by_trim = 0
        monthly_payment = 0
        residual_value = 0

        try:  # 첫번째 업체 유무
            price_compare_company_1 = soup.select(
                '#rentLeaserResult > div.re_call > div.reh_con_list > div:nth-child(2) > div.ri_img_title > div.right > div > strong > span')[
                0].get_text()
            price_compare_list.append(int(re.sub(r',', '', price_compare_company_1)))
        except:
            is_problem += '가격 비교 업체 없음'

            # 다나와 직영몰 월 납부금으로 대체(월 납부금 -5만원 적용)
            price_compare_list.append(int(re.sub(r',', '',
                                                 soup.select(
                                                     '#rentLeaserResult > div.re_directmall > div.reh_con_list > div > div.ri_img_title > div.right > div > strong > span')[
                                                     0].get_text())) - 50000)

            # 자세히 버튼 클릭
            driver.find_element_by_css_selector(
                '#rentLeaserResult > div.re_directmall > div.reh_con_list > div > div.ri_img_title > div.left > ul > li.ri_info_list.ri_info_color3 > a').click()

            # 직영몰 잔존가치
            src2 = driver.page_source
            soup = BeautifulSoup(src2)
            residual_value = soup.select(
                '#layerPopup > div.g-layer__wrap.draggable.ui-draggable.ui-draggable-handle > div.g-layer__cont > div > table:nth-child(1) > tbody > tr:nth-child(3) > td')[
                0].get_text()

        try:  # 두번재 업체 유무
            price_compare_company_2 = soup.select(
                '#rentLeaserResult > div.re_call > div.reh_con_list > div:nth-child(4) > div.ri_img_title > div.right > div > strong > span')[
                0].get_text()
            price_compare_list.append(int(re.sub(r',', '', price_compare_company_2)))
        except:
            is_problem += '2순위 업체 없음'

        try:
            driver.find_element_by_css_selector(
                '#rentLeaserResult > div.re_call > div.reh_con_list > div:nth-child(2) > div.ri_img_title > div.left > ul > li.ri_info_list.ri_info_color3 > a').click()
            src2 = driver.page_source
            soup = BeautifulSoup(src2)
            residual_value = soup.select(
                '#layerPopup > div.g-layer__wrap.draggable.ui-draggable.ui-draggable-handle > div.g-layer__cont > div > table:nth-child(1) > tbody > tr:nth-child(3) > td')[
                0].get_text()
        except:
            pass

        price_by_trim = int(re.sub(r',', '', TRIMS[trimcode]['price']))
        monthly_payment = sum(price_compare_list) / len(price_compare_list)
        residual_value = int(re.sub(r',', '', str(residual_value)))

        EACH_ROW.append({'수입 구분': is_imported,
                         '브랜드 명칭': brand_key,
                         '모델 명칭': MODELS[model_code],
                         '라인업 명칭': TRIMS[trimcode]['lineup_name'],
                         '트림 명칭': TRIMS[trimcode]['trim_name'],
                         '브랜드 코드': brand_val,
                         '모델 코드': model_code,
                         '라인업 코드': TRIMS[trimcode]['lineup_code'],
                         '트림 코드': trimcode,
                         '상품 구분': prodtype,
                         '할부 기간': period,
                         '가격타입': pricetype,
                         '월 납부금': round(monthly_payment),
                         '잔존가치': residual_value,
                         '취득원가': round(
                             (monthly_payment * period) + residual_value + (residual_value * 7 / 100)),
                         '비고': is_problem
                         })
        print(EACH_ROW[-1])
        return False

    else:
        return True  # true일 때 loop break 실행됌


for item in BRANDS:
    is_imported = str(list(item.keys())[0])  # 수입 여부 dict_keys to str
    for brand_by_contries in item.values():
        for BRAND_key, BRAND_val in brand_by_contries.items():

            sale_cars = get_model_info(BRAND_val)
            MODELS = {}  # 모델 dict 초기화
            for each_model in sale_cars:
                is_problem = each_model['class']  # 예정이거나 재고인 차량 제외
                if not is_problem:
                    MODELS[each_model['code']] = each_model.find('span').get_text()

            print('START : {}'.format(BRAND_key))
            for model_code in MODELS.keys():
                model_trim_list = get_model_trims(model_code)
                TRIMS = {}  # TRIMS를 다시 비움
                for each_trim in model_trim_list[0].select('li'):
                    trim_code = re.search(r'[0-9]+', str(each_trim.find('input')['class'])).group()
                    lineup_name = each_trim.find('input')['trimname']
                    lineup_code = each_trim.find('input')['lineup']
                    trim_name = each_trim.find('input')['trimnamet']
                    price = each_trim.find(class_='item price').get_text()

                    TRIMS[trim_code] = {'lineup_name': lineup_name,
                                        'lineup_code': lineup_code,
                                        'trim_name': trim_name,
                                        'price': price}

                driver = webdriver.Chrome(chrome_driver)

                trigger = ''
                for trimcode in TRIMS.keys():
                    for prodtype in PRODTYPE:
                        if trigger:
                            break
                        for period in PERIOD:
                            if trigger:
                                break
                            for pricetype in PRICETYPE:
                                trigger = get_target_prices(is_imported, BRAND_key, BRAND_val, model_code, trimcode,
                                                            prodtype, period, pricetype)
                                time.sleep(1)

                                if trigger:
                                    break

                time.sleep(1.5)
                driver.close()

            print('END : {}'.format(BRAND_key))


# 고정 값으로 dataframe에 append할 항목
EXTRA_DESCRIPTION = {'국산': '최신형 2채널 블랙박스, 썬팅(전면,측후면), 코일매트',
                    '수입': '최신형 2채널 블랙박스, 썬팅(전면,측후면), 하이패스, 유리막코팅, 생활보호PPF필름'}
CONTRACT_FEE = 'Y'
CONTRACT_DISTANCE = '20000'
PROMOTIONS = 'Y'

df = pd.DataFrame(EACH_ROW)

df['중도해지수수료'] = CONTRACT_FEE
df['약정거리'] = CONTRACT_DISTANCE
df['해택유무'] = PROMOTIONS

df['부가설명'] = [EXTRA_DESCRIPTION['국산'] if col == '국산' else EXTRA_DESCRIPTION['수입'] for col in df['수입 구분']]

writer = pd.ExcelWriter('danawa_auto_result.xlsx', engine='xlsxwriter')

df.to_excel(writer, sheet_name='test')
writer.close()