import json
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import Lead

@csrf_exempt
def generate_leads(request):
    """
    API endpoint to generate leads based on search criteria.
    Accepts POST request with company size, industry, and location.
    Returns JSON with enriched leads and personalized messages.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        # Parse input (hardcoded for demo, can be extended to accept JSON)
        search_criteria = {
            'company_size': '1-1000',  # Broader range
            'industry': 'retail',      # Wider category
            'location': 'Europe'       # Broader location
        }

        # Step 1: Fetch leads from Apollo API
        apollo_url = 'https://api.apollo.io/v1/organizations/search'
        headers = {
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache',
            'X-Api-Key': settings.APOLLO_API_KEY
        }
        payload = {
            'per_page': 10,
            'organization_num_employees_ranges': [search_criteria['company_size']],
            'organization_industries': [search_criteria['industry']],
            'organization_locations': [search_criteria['location']]
        }

        response = requests.post(apollo_url, headers=headers, json=payload)
        response.raise_for_status()
        apollo_data = response.json()
        print("Apollo Response:", apollo_data)  # Debug: Print full response

        leads = []
        for organization in apollo_data.get('organizations', [])[:5]:  # Limit to 5 leads
            company_name = organization.get('name', 'Unknown')
            website = organization.get('website_url', '')
            print(f"Processing: {company_name}, Website: {website}")  # Debug: Track each organization
            if not website:
                print(f"Skipping {company_name} due to no website")
                continue

            # Step 2: Scrape company website for insights
            if 'louisvuitton' in website.lower():
                insights = "Scraping restricted for this site. Using default insight."
            else:
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                    web_response = requests.get(website, headers=headers, timeout=5)
                    web_response.raise_for_status()
                    soup = BeautifulSoup(web_response.content, 'html.parser')
                    paragraphs = soup.find_all('p')
                    insights = ' '.join(p.get_text() for p in paragraphs[:3])[:500]
                except Exception as e:
                    insights = f"Scraping failed: {str(e)}. Using default insight."

            # Step 3: Generate personalized outreach message
            openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
            prompt = (
                f"You are a sales representative for a hardware computer store. "
                f"Generate a professional B2B outreach message for {company_name}, "
                f"a {search_criteria['industry']} company with {search_criteria['company_size']} employees. "
                f"Use these insights from their website: {insights[:200]}. "
                f"Highlight relevant hardware solutions (e.g., servers, workstations) and keep the tone professional."
            )
            try:
                completion = openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=150
                )
                message = completion.choices[0].message.content.strip()
            except Exception as e:
                message = f"Failed to generate message: {str(e)}"

            # Step 4: Store lead in database
            lead = Lead.objects.create(
                company_name=company_name,
                website=website,
                employee_count=organization.get('estimated_num_employees', 0),
                scraped_insights=insights,
                personalized_message=message
            )

            leads.append({
                'company_name': company_name,
                'website': website,
                'employee_count': organization.get('estimated_num_employees', 0),
                'scraped_insights': insights,
                'personalized_message': message
            })

        # Step 5: Save leads to JSON file
        with open('leads_output.json', 'w') as f:
            json.dump(leads, f, indent=4)

        return JsonResponse({'leads': leads}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
# import json
# import requests
# from bs4 import BeautifulSoup
# from openai import OpenAI
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from django.conf import settings
# from .models import Lead
# @csrf_exempt
# def generate_leads(request):
#     """
#     API endpoint to generate leads based on search criteria.
#     Accepts POST request with company size, industry, and location.
#     Returns JSON with enriched leads and personalized messages.
#     """
#     if request.method != 'POST':
#         return JsonResponse({'error': 'Method not allowed'}, status=405)

#     try:
#         # Parse input (hardcoded for demo, can be extended to accept JSON)
#         search_criteria = {
#             'company_size': '1-1000',  # Broader range
#             'industry': 'retail',  # Wider category
#             'location': 'Europe'      # Broader location
#         }

#         # Step 1: Fetch leads from Apollo API
#         apollo_url = 'https://api.apollo.io/v1/organizations/search'
#         headers = {
#             'Content-Type': 'application/json',
#             'Cache-Control': 'no-cache',
#             'X-Api-Key': settings.APOLLO_API_KEY
#         }
#         payload = {
#             'per_page': 10,
#             'organization_num_employees_ranges': [search_criteria['company_size']],
#             'organization_industries': [search_criteria['industry']],
#             'organization_locations': [search_criteria['location']]
#         }

#         response = requests.post(apollo_url, headers=headers, json=payload)
#         response.raise_for_status()
#         apollo_data = response.json()
#         print("Apollo Response:", apollo_data)  # Debug: Print full response

#         leads = []
#         for organization in apollo_data.get('organizations', [])[:5]:  # Limit to 5 leads
#             company_name = organization.get('name', 'Unknown')
#             website = organization.get('website_url', '')
#             print(f"Processing: {company_name}, Website: {website}")  # Debug: Track each organization
#             if not website:
#                 print(f"Skipping {company_name} due to no website")
#                 continue

#             # Step 2: Scrape company website for insights
#             try:
#                 headers = {
#                 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
#                 }
#                 web_response = requests.get(website, timeout=5)
#                 web_response.raise_for_status()
#                 soup = BeautifulSoup(web_response.content, 'html.parser')
#                 paragraphs = soup.find_all('p')
#                 insights = ' '.join(p.get_text() for p in paragraphs[:3])[:500]
#             except Exception as e:
#                 insights = f"Could not scrape website: {str(e)}"

#             # Step 3: Generate personalized outreach message
#             openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
#             prompt = (
#                 f"You are a sales representative for a hardware computer store. "
#                 f"Generate a professional B2B outreach message for {company_name}, "
#                 f"a {search_criteria['industry']} company with {search_criteria['company_size']} employees. "
#                 f"Use these insights from their website: {insights[:200]}. "
#                 f"Highlight relevant hardware solutions (e.g., servers, workstations) and keep the tone professional."
#             )
#             try:
#                 completion = openai_client.chat.completions.create(
#                     model="gpt-3.5-turbo",
#                     messages=[{"role": "user", "content": prompt}],
#                     max_tokens=150
#                 )
#                 message = completion.choices[0].message.content.strip()
#             except Exception as e:
#                 message = f"Failed to generate message: {str(e)}"

#             # Step 4: Store lead in database
#             lead = Lead.objects.create(
#                 company_name=company_name,
#                 website=website,
#                 employee_count=organization.get('estimated_num_employees', 0),
#                 scraped_insights=insights,
#                 personalized_message=message
#             )

#             leads.append({
#                 'company_name': company_name,
#                 'website': website,
#                 'employee_count': organization.get('estimated_num_employees', 0),
#                 'scraped_insights': insights,
#                 'personalized_message': message
#             })

#         # Step 5: Save leads to JSON file
#         with open('leads_output.json', 'w') as f:
#             json.dump(leads, f, indent=4)

#         return JsonResponse({'leads': leads}, status=200)

#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=500)
# # @csrf_exempt
# # def generate_leads(request):
# #     """
# #     API endpoint to generate leads based on search criteria.
# #     Accepts POST request with company size, industry, and location.
# #     Returns JSON with enriched leads and personalized messages.
# #     """
# #     if request.method != 'POST':
# #         return JsonResponse({'error': 'Method not allowed'}, status=405)

# #     try:
# #         # Parse input (hardcoded for demo, can be extended to accept JSON)
# #         search_criteria = {
# #             'company_size': '1-1000',  # Broader range
# #             'industry': 'technology',  # Wider category
# #             'location': 'global'      # Broader location
# #         }

# #         # Step 1: Fetch leads from Apollo API
# #         apollo_url = 'https://api.apollo.io/v1/organizations/search'
# #         headers = {
# #             'Content-Type': 'application/json',
# #             'Cache-Control': 'no-cache',
# #             'X-Api-Key': settings.APOLLO_API_KEY
# #         }
# #         payload = {
# #             'per_page': 10,
# #             'organization_num_employees_ranges': [search_criteria['company_size']],
# #             'organization_industries': [search_criteria['industry']],
# #             'organization_locations': [search_criteria['location']]
# #         }

# #         response = requests.post(apollo_url, headers=headers, json=payload)
# #         response.raise_for_status()
# #         apollo_data = response.json()

# #         leads = []
# #         for organization in apollo_data.get('organizations', [])[:5]:  # Limit to 5 leads
# #             company_name = organization.get('name', 'Unknown')
# #             website = organization.get('website_url', '')
# #             print(f"Company: {company_name}, Website: {website}")  # Add this line
# #             if not website:
# #                 continue

# #             # Step 2: Scrape company website for insights
# #             try:
# #                 web_response = requests.get(website, timeout=5)
# #                 web_response.raise_for_status()
# #                 soup = BeautifulSoup(web_response.content, 'html.parser')
# #                 # Extract text from paragraphs (simplified scraping)
# #                 paragraphs = soup.find_all('p')
# #                 insights = ' '.join(p.get_text() for p in paragraphs[:3])[:500]
# #             except Exception as e:
# #                 insights = f"Could not scrape website: {str(e)}"

# #             # Step 3: Generate personalized outreach message
# #             openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
# #             prompt = (
# #                 f"You are a sales representative for a hardware computer store. "
# #                 f"Generate a professional B2B outreach message for {company_name}, "
# #                 f"a {search_criteria['industry']} company with {search_criteria['company_size']} employees. "
# #                 f"Use these insights from their website: {insights[:200]}. "
# #                 f"Highlight relevant hardware solutions (e.g., servers, workstations) and keep the tone professional."
# #             )
# #             try:
# #                 completion = openai_client.chat.completions.create(
# #                     model="gpt-3.5-turbo",
# #                     messages=[{"role": "user", "content": prompt}],
# #                     max_tokens=150
# #                 )
# #                 message = completion.choices[0].message.content.strip()
# #             except Exception as e:
# #                 message = f"Failed to generate message: {str(e)}"

# #             # Step 4: Store lead in database
# #             lead = Lead.objects.create(
# #                 company_name=company_name,
# #                 website=website,
# #                 employee_count=organization.get('estimated_num_employees', 0),
# #                 scraped_insights=insights,
# #                 personalized_message=message
# #             )

# #             leads.append({
# #                 'company_name': company_name,
# #                 'website': website,
# #                 'employee_count': organization.get('estimated_num_employees', 0),
# #                 'scraped_insights': insights,
# #                 'personalized_message': message
# #             })

# #         # Step 5: Save leads to JSON file
# #         with open('leads_output.json', 'w') as f:
# #             json.dump(leads, f, indent=4)

# #         return JsonResponse({'leads': leads}, status=200)

# #     except Exception as e:
# #         return JsonResponse({'error': str(e)}, status=500)