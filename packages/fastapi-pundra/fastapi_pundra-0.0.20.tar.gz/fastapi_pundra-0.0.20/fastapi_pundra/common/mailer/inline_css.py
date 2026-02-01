import os
from bs4 import BeautifulSoup
from premailer import Premailer
from fastapi_pundra.common.helpers import base_path
from dotenv import load_dotenv

load_dotenv()

def inline_css(html_code):
    # Parse the HTML code
    soup = BeautifulSoup(html_code, 'html.parser')

    # Find all link tags with a "stylesheet" rel attribute
    link_tags = soup.find_all('link', rel='stylesheet')

    # Extract the href attribute values
    css_files = [link['href'] for link in link_tags]

    project_base_path = os.getenv('PROJECT_BASE_PATH', 'app')

    # Read the content of each CSS file and include it in the HTML
    mail_template_dir = os.path.join(base_path(), project_base_path, 'templates', 'mails')
    for css_file in css_files:
        css_file_path = os.path.join(mail_template_dir, css_file)
        # Check if the file exists
        if os.path.exists(css_file_path):
            with open(css_file_path, 'r') as file:
                css_content = file.read()
                # Create a new style tag with the CSS content
                style_tag = soup.new_tag('style')
                style_tag.string = css_content
                # Replace the link tag with the new style tag
                link_tag = soup.find('link', href=css_file)
                link_tag.replace_with(style_tag)
        else:
            print('file not found')
            pass
          
    for tag in link_tags:
        tag.extract()

    # Get the modified HTML as a string
    modified_html = str(soup)
    
    # ascii issue: https://github.com/peterbe/premailer/issues/249#issuecomment-1541119706
    the_html_with_ascii = modified_html.encode("ascii", "xmlcharrefreplace").decode("ascii")
    
    # intance of premailer.
    premailer_instance = Premailer(
        the_html_with_ascii,
        strip_important=False,
        remove_classes=True
      )
    
    processed_html = premailer_instance.transform()

    return processed_html