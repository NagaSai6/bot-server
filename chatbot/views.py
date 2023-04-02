from django.shortcuts import render
from django.http import HttpResponse,JsonResponse 
import requests
from bs4 import BeautifulSoup
import time
from django.views.decorators.csrf import csrf_exempt
from urllib import parse, request
import html
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
import os 
import base64
from datetime import datetime
import json
# Create your views here.
# req => response 
# request handler




def say_hello(request):
    #pull db from db
    return render(request,'hello.html',{'name':'Naga'})

def is_valid_url(url):
    """
    Checks if a URL is valid
    """
    try:
        result = parse.urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

# def scrape_content(url, headers):
#     try:
#         response = requests.get(url, headers=headers)
#     except requests.exceptions.RequestException:
#         return None

#     soup = BeautifulSoup(response.content, 'html.parser')
#     content = soup.get_text()

#     return content
def scrape_content(url, headers):
    try:
        response = requests.get(url, headers=headers)
    except requests.exceptions.RequestException:
        return None

    soup = BeautifulSoup(response.content, 'html.parser')

    # Skip img, svg, and icon tags
    for tag in soup.find_all(['img', 'svg', 'icon']):
        tag.decompose()

    # Extract text from remaining tags and unescape HTML entities
    content = ''.join(html.unescape(s).strip() for s in soup.stripped_strings)

    return content

def scrape_website(url, headers):
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')

        links = []
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and href.startswith(url):
                links.append(href)

        content = scrape_content(url, headers)
        if not content:
            return None

        for link in links:
            time.sleep(1)  # add a delay between requests
            link_content = scrape_content(link, headers)
            if link_content:
                content += link_content

        return content
    except requests.exceptions.RequestException:
        return None
    

def send_mail(data):
    # Configure API key authorization: api-key
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = os.environ.get('SENDIN_BLUE_API')
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
    filename = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
    file_content = data.encode('utf-8')
    encoded_content = base64.b64encode(file_content).decode('utf-8')
    # Define email details
    email_to = [{'email': 'ch18b053@smail.iitm.ac.in'}, {'email': 'ch18b054@smail.iitm.ac.in'}]
    email_subject = 'Scraped Data'
    email_text = 'Here is the scraped data in text format.'
    email_sender = {'name': 'Naga Sai', 'email': 'nagasai317@gmail.com'}
    email_attachment = [
        {
                'content': encoded_content,
                'name': filename,
                'type': 'text/plain'
            }
    ]
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(to=email_to, subject=email_subject, text_content=email_text, sender=email_sender, attachment=email_attachment)
    try:
    # Send the email message
        api_response = api_instance.send_transac_email(send_smtp_email)
        return JsonResponse({'success': True, 'message': 'Email sent successfully'})
    except ApiException as e:
        return JsonResponse({'success': False, 'error': 'Failed to send email: {}'.format(str(e))})   

@csrf_exempt
def form_submission_api(request):
    if request.method == 'POST':
        url = request.POST.get('url')
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

        if not is_valid_url(url):
            return JsonResponse({'success': False, 'error': 'Invalid URL'})

        content = scrape_website(url, headers)
        if not content:
            return JsonResponse({'success': False, 'error': 'Unable to scrape website'})
        # content = content[:1500]
        response = send_mail(content)
        # response_json = json.dumps(response)
        return JsonResponse({'success': True, 'content': len(content)})
    else:
        return JsonResponse({'success': False, 'error': 'Method not allowed'})