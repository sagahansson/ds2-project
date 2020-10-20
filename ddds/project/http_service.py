# -*- coding: utf-8 -*-

import json

from flask import Flask, request
from urllib.request import Request, urlopen
from jinja2 import Environment
#from restcountries import RestCountryApiV2 as rapi

app = Flask(__name__)
environment = Environment()


def jsonfilter(value):
    return json.dumps(value)


environment.filters["json"] = jsonfilter


def error_response(message):
    response_template = environment.from_string("""
    {
      "status": "error",
      "message": {{message|json}},
      "data": {
        "version": "1.0"
      }
    }
    """)
    payload = response_template.render(message=message)
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    return response


def query_response(value, grammar_entry):
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.1",
        "result": [
          {
            "value": {{value|json}},
            "confidence": 1.0,
            "grammar_entry": {{grammar_entry|json}}
          }
        ]
      }
    }
    """)
    payload = response_template.render(value=value, grammar_entry=grammar_entry)
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    return response


def multiple_query_response(results):
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.0",
        "result": [
        {% for result in results %}
          {
            "value": {{result.value|json}},
            "confidence": 1.0,
            "grammar_entry": {{result.grammar_entry|json}}
          }{{"," if not loop.last}}
        {% endfor %}
        ]
      }
    }
     """)
    payload = response_template.render(results=results)
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    return response


def validator_response(is_valid):
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.0",
        "is_valid": {{is_valid|json}}
      }
    }
    """)
    payload = response_template.render(is_valid=is_valid)
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    return response


@app.route("/dummy_query_response", methods=['POST'])
def dummy_query_response():
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.1",
        "result": [
          {
            "value": "dummy",
            "confidence": 1.0,
            "grammar_entry": null
          }
        ]
      }
    }
     """)
    payload = response_template.render()
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    return response


@app.route("/action_success_response", methods=['POST'])
def action_success_response():
    response_template = environment.from_string("""
   {
     "status": "success",
     "data": {
       "version": "1.1"
     }
   }
   """)
    payload = response_template.render()
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    return response

def get_data(code, search_by='alpha'):
    #key = sagakey
    url = f"https://restcountries.eu/rest/v2/{search_by}/{code}"
    print(url)
    request = Request(url)
    response = urlopen(request)
    data = response.read()
    print(json.loads(data))
    return json.loads(data)


@app.route("/population", methods=['POST'])
def population():
  payload = request.get_json()
  country = payload['context']['facts']['selected_country']['value']
  print("payload: ", payload)
  data = get_data(country)['population']
  print(data)
  #data = rapi.get_country_by_country_code(country).population
  if 6 < len(str(data)) < 10:
    data = round((data/1000000), 2)
    data = str(data) + " Million"
  elif len(str(data)) >= 10:
    data = round((data/1000000000), 2)
    data = str(data) + " Billion"
  else:
    data = str(data)
    print(data)
  return query_response(value=data, grammar_entry=None)

@app.route("/neighbours", methods=['POST'])
def neighbours():
  payload = request.get_json()
  country = payload['context']['facts']['selected_country']['value']
  print("payload: ", payload)
  data = get_data(country)['borders']
  data = [get_data(neighbour)['name'] for neighbour in data]
  if len(data) > 1:
    last_two = data[-2:] # or only two if len(data) = 2
    data = [n + ',' for n in data[:-2]]
    data.extend(last_two)
    data.insert(-1, 'and')
  data = ' '.join(data)
  print(data)
  return query_response(value=data, grammar_entry=None)

def get_simple(subject):
  # simplest data fetching function, used when no conditions are needed etc
  payload = request.get_json()
  country = payload['context']['facts']['selected_country']['value']
  data = get_data(country)[subject]
  return data

@app.route("/capital", methods=['POST'])
def capital():
  data = get_simple('capital')
  return query_response(value=data, grammar_entry=None)

@app.route("/size", methods=['POST'])
def size():
  data = str(int(get_simple('area'))) + ' square kilometers'
  return query_response(value=data, grammar_entry=None)

@app.route("/continent", methods=['POST'])
def continent():
  data = get_simple('region')
  return query_response(value=data, grammar_entry=None)


@app.route("/language", methods=['POST'])
def language():
  payload = request.get_json()
  country = payload['context']['facts']['selected_country']['value']
  print("payload: ", payload)
  data = get_data(country)['languages']
  data = [lang['name'] for lang in data]
  if len(data) > 1:
    last_two = data[-2:] # or only two if len(data) = 2
    data = [n + ',' for n in data[:-2]]
    data.extend(last_two)
    data.insert(-1, 'and')
  data = ' '.join(data)
  print(data)
  return query_response(value=data, grammar_entry=None)

