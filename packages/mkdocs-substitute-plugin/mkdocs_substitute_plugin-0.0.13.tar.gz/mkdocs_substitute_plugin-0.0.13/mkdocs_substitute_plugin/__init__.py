import feedparser
import json
from mkdocs.plugins import BasePlugin
from mkdocs.config import config_options
from bs4 import BeautifulSoup

import os
import random
import string

from datetime import datetime

import locale
locale.setlocale(locale.LC_TIME, "de_DE.UTF-8")
from email.utils import parsedate_to_datetime

import logging
log = logging.getLogger("mkdocs.plugins.substitute")
log.setLevel(logging.DEBUG)
log.debug("Substitution wird ausgeführt")

class SubstitutePlugin(BasePlugin):
    config_scheme = (
        ('substitutions_file', config_options.Type(str, default='substitutions.json')),
    )

    def on_config(self, config):
        # Pfad relativ zu mkdocs.yml auflösen
        base_dir = os.path.dirname(config.config_file_path)
        file_path = os.path.join(base_dir, self.config['substitutions_file'])

        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Substitutions-File not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            self.substitutions = json.load(f)

        return config
    
    # -------------------------------------------------------------------------------
    # SEO PLUGIN - Subfunktion von Substitute
    # -------------------------------------------------------------------------------

    def on_post_page(self, output, page, config):
        soup = BeautifulSoup(output, 'html.parser')

        # Metadaten aus der YAML-Präambel
        description = page.meta.get('description')
        keywords = page.meta.get('keywords')
        robots = page.meta.get('robots')
        og_type = page.meta.get('og_type')
        og_title = page.meta.get('og_title')
        og_description = page.meta.get('og_description')
        og_image = page.meta.get('og_image')
        og_url = page.meta.get('og_url')
        og_sitename = page.meta.get('og_sitename')       
        canonical = page.meta.get('canonical')       
        

        # Head-Bereich finden
        head = soup.find('head')
        if head:
            if description:
                meta_desc = soup.new_tag('meta', attrs={
                    'name': 'description',
                    'content': description
                })
                if not soup.find('meta', attrs={'name': 'description'}):
                    # Nur einfügen, wenn nicht vorhanden
                    head.append(meta_desc)                

            if keywords:
                # Unterstützt Liste oder String
                keyword_str = ', '.join(keywords) if isinstance(keywords, list) else str(keywords)
                meta_keywords = soup.new_tag('meta', attrs={
                    'name': 'keywords',
                    'content': keyword_str
                })
                head.append(meta_keywords)
                
                # <meta name="robots" content="index, follow">
            if robots:
                meta_desc = soup.new_tag('meta', attrs={
                    'name': 'robots',
                    'content': robots
                })
                if not soup.find('meta', attrs={'name': 'robots'}):
                    # Nur einfügen, wenn nicht vorhanden
                    head.append(meta_desc)  

            if og_type:   
                meta_desc = soup.new_tag('meta', attrs={
                    'property': 'og:type',
                    'content': og_type
                })
                if not soup.find('meta', attrs={'property': 'og:type'}):
                    # Nur einfügen, wenn nicht vorhanden
                    head.append(meta_desc)  

            if og_title:   
                meta_desc = soup.new_tag('meta', attrs={
                    'property': 'og:title',
                    'content': og_title
                })
                if not soup.find('meta', attrs={'property': 'og:title'}):
                    # Nur einfügen, wenn nicht vorhanden
                    head.append(meta_desc)        
                    
            if og_description:   
                meta_desc = soup.new_tag('meta', attrs={
                    'property': 'og:description',
                    'content': og_description
                })
                if not soup.find('meta', attrs={'property': 'og:description'}):
                    # Nur einfügen, wenn nicht vorhanden
                    head.append(meta_desc)                 

            if og_image:   
                meta_desc = soup.new_tag('meta', attrs={
                    'property': 'og:image',
                    'content': og_image
                })
                if not soup.find('meta', attrs={'property': 'og:image'}):
                    # Nur einfügen, wenn nicht vorhanden
                    head.append(meta_desc)      
                    
            if og_url:   
                meta_desc = soup.new_tag('meta', attrs={
                    'property': 'og:url',
                    'content': og_url
                })
                if not soup.find('meta', attrs={'property': 'og:url'}):
                    # Nur einfügen, wenn nicht vorhanden
                    head.append(meta_desc)                        
                    
            if og_sitename:   
                meta_desc = soup.new_tag('meta', attrs={
                    'property': 'og:sitename',
                    'content': og_sitename
                })
                if not soup.find('meta', attrs={'property': 'og:sitename'}):
                    # Nur einfügen, wenn nicht vorhanden
                    head.append(meta_desc)                        
                
            if canonical:   
                meta_desc = soup.new_tag('link', attrs={
                    'rel': 'canonical',
                    'href': canonical
                })
                if not soup.find('meta', attrs={'rel': 'canonical'}):
                    # Nur einfügen, wenn nicht vorhanden
                    head.append(meta_desc)                        


        return str(soup)


    
    #def on_page_content(self, html, page, config, files):
        #header_html = '<div style=="background-color: #fff3cd; padding: 0.75em;  border-bottom: 1px solid #f0ad4e;  font-weight: bold;  text-align: center;>Das ist ein Test</div>'
        #return header_html + html

    def on_page_markdown(self, markdown, page, config, files):
        for key, value in self.substitutions.items():
            check_key = key[:6]
            #log.debug("Substitution check_key : " + check_key)
            match check_key:
                # ------------------------------------------------------------------------------            
                # ICON from Pictogrammers
                # ------------------------------------------------------------------------------            
                case "[icon_":
                    new_value = '<span class="mdi mdi-' + value +'"></span>'
                    markdown = markdown.replace(key, new_value)        

                # ------------------------------------------------------------------------------            
                # CARDS
                # ------------------------------------------------------------------------------            
                
                # ----- cardA
                case "[cardA":

                    html_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

                    # Default Values setzen, falls nicht in Settings
                    the_title = "CARD TITLE"
                    the_text = "Lorem ipsum dolor sit amet consectetur adipisicing elit. Vel, voluptatum. Magni hic, voluptate debitis esse corporis dolor laudantium quae quo!"
                    the_icon = "laptop"
                    the_width = "auto"
                    the_padding = "2.5rem"
                    the_gradient_background_color1 = "#e0e4e5"
                    the_gradient_background_color2 = "#f2f6f9"
                    the_gradient_element = "red, blue"
                    the_shadow_flag = "true"

                    # Values auslesen und damit Defaults überschreiben
                    for subkey, subvalue in value.items():
                        if subkey == "title":
                            the_title = subvalue
                        if subkey == "text":
                            the_text = subvalue
                        if subkey == "icon":
                            the_icon = subvalue
                        if subkey == "width":
                            the_width = subvalue    
                        if subkey == "padding":
                            the_padding = subvalue
                        if subkey == "gradient_background_color1":
                            the_gradient_background_color1 = subvalue
                        if subkey == "gradient_background_color2":
                            the_gradient_background_color2 = subvalue 
                        if subkey == "gradient_colors_element":
                            the_gradient_element = subvalue     
                        if subkey == "enable_shadow":
                            the_shadow_flag = subvalue

                    if the_shadow_flag == "true":
                        new_value = ('<style>'
                        '.cardA_card_' + html_id + '{ --grad: ' + the_gradient_element + ';  background-image: linear-gradient(to bottom left, ' + the_gradient_background_color1 + ',' + the_gradient_background_color2 + '); border-radius: 2rem; gap: 1.5rem; display: grid; grid-template: "title icon" "content content" "bar bar" / 1fr auto; font-family: system-ui, sans-serif; color: #444447; box-shadow: inset -2px 2px hsl(0 0 100% / 1), -20px 20px 40px hsl(0 0 0 / .25) ;' 
                        
                        '.cardA_title_' + html_id + '{ font-size: 1.5rem; grid-area: title; align-self: end; text-transform: uppercase; font-weight: 500; word-break: break-all; } .cardA_icon_' + html_id + '{ grid-area: icon; font-size: 3rem; > span { color: transparent; background: linear-gradient(to right, var(--grad)); background-clip: text; } }'
                        
                        '.cardA_content_' + html_id + '{ grid-area: content; & > *:first-child { margin-top: 0rem} & > *:last-child { margin-bottom: 0rem} } &::after { content: ""; grid-area: bar; height: 2px; background-image: linear-gradient(90deg, var(--grad)); } } '
                        
                        '</style>'
                        
                        '<div style="width: ' + the_width + ';"><div class="cardA_card_' + html_id +'" style="padding: ' + the_padding +';">'
                        '<div class="cardA_title_' + html_id + '">' + the_title + '</div> '
                        '<div class="cardA_icon_' + html_id +'"><span class="mdi mdi-' + the_icon + '"></span></div> '
                        '<div class="cardA_content_' + html_id +'"> <p>' + the_text + '</p> </div> </div></div>')
                    else:
                        new_value = ('<style>'
                        '.cardA_card_' + html_id + '{ --grad: ' + the_gradient_element + ';  background-image: linear-gradient(to bottom left, ' + the_gradient_background_color1 + ',' + the_gradient_background_color2 + '); border-radius: 2rem; gap: 1.5rem; display: grid; grid-template: "title icon" "content content" "bar bar" / 1fr auto; font-family: system-ui, sans-serif; color: #444447;' 
                        
                        '.cardA_title_' + html_id + '{ font-size: 1.5rem; grid-area: title; align-self: end; text-transform: uppercase; font-weight: 500; word-break: break-all; } .cardA_icon_' + html_id + '{ grid-area: icon; font-size: 3rem; > span { color: transparent; background: linear-gradient(to right, var(--grad)); background-clip: text; } }'
                        
                        '.cardA_content_' + html_id + '{ grid-area: content; & > *:first-child { margin-top: 0rem} & > *:last-child { margin-bottom: 0rem} } &::after { content: ""; grid-area: bar; height: 2px; background-image: linear-gradient(90deg, var(--grad)); } } '
                        
                        '</style>'
                        
                        '<div style="width: ' + the_width + ';"><div class="cardA_card_' + html_id +'" style="padding: ' + the_padding +';">'
                        '<div class="cardA_title_' + html_id + '">' + the_title + '</div> '
                        '<div class="cardA_icon_' + html_id +'"><span class="mdi mdi-' + the_icon + '"></span></div> '
                        '<div class="cardA_content_' + html_id +'"> <p>' + the_text + '</p> </div> </div></div>')
                    
                    markdown = markdown.replace(key, new_value)           
                
                # ----- cardA
                case "[cardB":       

                    html_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

                    # Default Values setzen, falls nicht in Settings
                    the_title = "CARD TITLE"
                    the_text = "Lorem ipsum dolor sit amet consectetur adipisicing elit. Vel, voluptatum. Magni hic, voluptate debitis esse corporis dolor laudantium quae quo!"
                    the_icon = "laptop"
                    the_width = "auto"
                    the_padding = "2.5rem"
                    the_gradient_background_color1 = "#e0e4e5"
                    the_gradient_background_color2 = "#f2f6f9"
                    the_gradient_element = "red, blue"

                    # Values auslesen und damit Defaults überschreiben
                    for subkey, subvalue in value.items():
                        if subkey == "title":
                            the_title = subvalue
                        if subkey == "text":
                            the_text = subvalue
                        if subkey == "icon":
                            the_icon = subvalue
                        if subkey == "width":
                            the_width = subvalue    
                        if subkey == "padding":
                            the_padding = subvalue
                        if subkey == "gradient_background_color1":
                            the_gradient_background_color1 = subvalue
                        if subkey == "gradient_background_color2":
                            the_gradient_background_color2 = subvalue 
                        if subkey == "gradient_colors_element":
                            the_gradient_element = subvalue    

                    new_value = ('<style>'
                    '.cardB_container  { transform: translate(-50%, -50%); height: 400px; width: 600px; background: #f2f2f2; overflow: hidden; border-radius: 20px; cursor: pointer; box-shadow: 0 0 20px 8px #d0d0d0; }'
                    '.cardB_content {  transform: translatey(-50%); text-align: justify; color: black; padding: 40px; font-family: "Merriweather", serif; }'     
                    '.cardB_h1 {  font-weight: 900;  text-align: center;}'
                    '.cardB_h3 {  font-weight: 300;}'
                    '.cardB_flap {  width: 100%;  height: 100%;}'
                    '.cardB_flap::before { content: ""; height: 100%; width: 50%; background: url("https://pbs.twimg.com/profile_images/1347260174176710658/2GfSZ1i__400x400.jpg") white; background-position: 100px; background-repeat: no-repeat; transition: 1s; }'
                    '.cardB_flap::after { content: ""; height: 100%; width: 50%; right: 0; background: url("https://pbs.twimg.com/profile_images/1347260174176710658/2GfSZ1i__400x400.jpg") white; background-position: -200px; background-repeat: no-repeat; transition: 1s; }'
                    '.cardB_container:hover .cardB_flap::after {  transform: translatex(300px);}'
                    '.cardB_container:hover .cardB_flap::before{  transform: translatex(-300px);}'
                    '</style>'
                    '<div class="cardB_container"> <div class="cardB_content">   <div class="cardB_h1">Pratham</div>    <div class="cardB_h3">I love designing websites and keep things as simple as possible. My goals is to focus on minimalism and conveying the message that you want to send</div>  </div>  <div class="cardB_flap"></div></div>')

                    markdown = markdown.replace(key, new_value)  
                                     
                # ------------------------------------------------------------------------------            
                # Bootstrap Alert Box - Nicht mehr genutzt
                # ------------------------------------------------------------------------------            
                case "[old_alert":           
                    # Values auslesen
                    for subkey, subvalue in value.items():
                        if subkey == "color":
                            the_color = subvalue
                        if subkey == "dismissible":
                            dismissible_flag = subvalue
                        if subkey == "text":
                            alert_text = subvalue

                    html_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
                    container_part = "<div id='bootstrap-container-" + html_id +"'></div>"
                    script_const = "<script>const container = document.getElementById('bootstrap-container-" + html_id + "');"
                    script_const_shadow = "const shadow = container.attachShadow({ mode: 'open' });"
                    alert_init = "script.onload = () => {const alertEl = shadow.querySelector('.alert'); const closeBtn = shadow.querySelector('.btn-close'); if (alertEl && closeBtn) { const bsAlert = new bootstrap.Alert(alertEl); closeBtn.addEventListener('click', () => {bsAlert.close();});}};"
                    script_shadow_inner = "shadow.innerHTML = `<link rel='stylesheet' href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css'>"
                    wrapper_tag =  "const script = document.createElement('script'); script.src = 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js';" + alert_init +"shadow.appendChild(script);"                        

                    if dismissible_flag == 'true':
                        shadow_inner_tag = '<div class="alert alert-' + the_color + ' alert-dismissible">' + alert_text + '<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>`;' + wrapper_tag +'</script>'
                    else:
                        shadow_inner_tag = '<div class="alert alert-' + the_color + '">' + alert_text + '</div>`;' + wrapper_tag + '</script>'
                    
                    new_value=container_part + script_const + script_const_shadow + script_shadow_inner + shadow_inner_tag
                    markdown = markdown.replace(key, new_value) 
                    
                case "[alert":           
                    # Values auslesen
                    for subkey, subvalue in value.items():
                        if subkey == "color":
                            the_color = subvalue
                        if subkey == "dismissible":
                            dismissible_flag = subvalue
                        if subkey == "text":
                            alert_text = subvalue

                    html_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

                    if the_color == 'success':
                        the_color = '#d1e7dd'

                    if the_color == 'info':
                        the_color = '#cff4fc'

                    if the_color == 'warning':
                        the_color = '#fff3cd'

                    if the_color == 'danger':                        
                        the_color = "#f8d7da"

                    if dismissible_flag == 'true':
                        new_value = (
                            '<style>'
                            '.alert_' + html_id +'{background-color: ' + the_color + '; position: relative; padding: 1rem 1.5rem; margin-bottom: 1rem; border: 1px solid transparent; border-radius: 0.375rem; font-family: system-ui, sans-serif;  line-height: 1.5;}'
                            '.alert_color_' + html_id +' {color: #0f5132; background-color: ' + the_color + '; border-color: #badbcc;}'
                            '.alert_' + html_id + ' .btn-close_' + html_id + '{ position: absolute;  top: 0.75rem;  right: 1rem;  padding: 0.25rem;  background: transparent;  border: none;  font-size: 1.00rem;  line-height: 1;  color: inherit;  cursor: pointer;}'    
                            '.alert_' + html_id + ' .btn-close_' + html_id + ':hover { opacity: 0.75;}'
                            '</style>'
                            '<div class="alert_' + html_id + ' alert-color_' + html_id +'">' + alert_text + '<button class="btn-close_' + html_id +'" onclick="this.parentElement.style.display=\'none\';">&times;</button></div>'
                            )
                    else:
                        new_value = (
                            '<style>'
                            '.alert_' + html_id + '{background-color: ' + the_color + '; position: relative; padding: 1rem 1.5rem; margin-bottom: 1rem; border: 1px solid transparent; border-radius: 0.375rem; font-family: system-ui, sans-serif;  line-height: 1.5;}'
                            '.alert_color_' + html_id + ' {color: #0f5132; background-color: ' + the_color + '; border-color: #badbcc;}'
                            '.alert_' + html_id + ' .btn-close_' + html_id + ' { position: absolute;  top: 0.75rem;  right: 1rem;  padding: 0.25rem;  background: transparent;  border: none;  font-size: 1.00rem;  line-height: 1;  color: inherit;  cursor: pointer;}'    
                            '.alert_' + html_id + ' .btn-close_' + html_id + ':hover { opacity: 0.75;}'
                            '</style>'
                            '<div class="alert_' + html_id + ' alert-color_' + html_id + '">' + alert_text +'</div>'
                            )
                        
                    markdown = markdown.replace(key, new_value)                     

                # ------------------------------------------------------------------------------            
                # ToolTip Notes
                # ------------------------------------------------------------------------------            
                case "[note_":       

                    html_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

                    # Default Values
                    the_text_hover = "Über diesem Text wird eine Notiz angezeigt"
                    the_text_note = "Das ist der Text der angezeigten Notiz"
                    make_italic_flag = "true"
                    the_cursor = "pointer"

                    # Values auslesen
                    for subkey, subvalue in value.items():
                        if subkey == "text_hover":
                            the_text_hover = subvalue
                        if subkey == "text_note":
                            the_text_note = subvalue  
                        if subkey == "make_italic":
                            make_italic_flag = subvalue  
                        if subkey == "cursor_style":
                            the_cursor = subvalue
                            
                    if make_italic_flag == "true":
                        new_value = (
                            '<style>'
                            '.sticky-note-container_' + html_id +' { position: relative; display: inline-block; cursor: ' + the_cursor + '; }'
                            '.sticky-note_' + html_id + '{ opacity: 0; transition: opacity 0.3s ease; width: 200px; background-color: #fff89a; color: #333; text-align: left; padding: 5px; border: 1px solid #e0c200; border-radius: 5px; box-shadow: 2px 2px 8px rgba(0,0,0,0.2); position: absolute; left: 50%; bottom: 100%; margin-bottom: 10px; z-index: 10; transform: translateX(-50%); font-family: "Arial", cursive, sans-serif; font-size: 13px;}'
                            '.sticky-note-container_' + html_id + ':hover .sticky-note_' + html_id +' { opacity: 1; }'
                            '</style>'
                            '<span class="sticky-note-container_' + html_id +'"><i>' + the_text_hover + ' </i><span class="sticky-note_' + html_id +'">' + the_text_note + '</span></span>' 
                            )
                    else:
                        new_value = (
                            '<style>'
                            '.sticky-note-container_' + html_id +' { position: relative; display: inline-block; cursor: ' + the_cursor + '; }'
                            '.sticky-note_' + html_id + '{ opacity: 0; transition: opacity 0.3s ease; width: 200px; background-color: #fff89a; color: #333; text-align: left; padding: 5px; border: 1px solid #e0c200; border-radius: 5px; box-shadow: 2px 2px 8px rgba(0,0,0,0.2); position: absolute; left: 50%; bottom: 100%; margin-bottom: 10px; z-index: 10; transform: translateX(-50%); font-family: "Arial", cursive, sans-serif; font-size: 13px;}'
                            '.sticky-note-container_' + html_id + ':hover .sticky-note_' + html_id + ' { opacity: 1; }'
                            '</style>'
                            '<span class="sticky-note-container_' + html_id +'">' + the_text_hover + ' <span class="sticky-note_' + html_id +'">' + the_text_note + '</span></span>' 
                            )
                                        
                    markdown = markdown.replace(key, new_value) 

                # ------------------------------------------------------------------------------            
                # Bootstrap Toast
                # ------------------------------------------------------------------------------            
                case "[toast":

                    # Default Values
                    title_text = "TOAST TITLE"
                    content = "This is the content of the TOAST"
                    background_color = "beige"
                    dismissible_flag = "true"

                    # Values auslesen
                    for subkey, subvalue in value.items():
                        if subkey == "title_text":
                            title_text = subvalue
                        if subkey == "content":
                            content = subvalue  
                        if subkey == "background_color":
                            background_color = subvalue  
                        if subkey == "dismissible":
                            dismissible_flag = subvalue

                    if background_color == 'success':
                        background_color = '#d1e7dd'

                    if background_color == 'info':
                        background_color = '#cff4fc'

                    if background_color == 'warning':
                        background_color = '#fff3cd'

                    if background_color == 'danger':                        
                        background_color = "#f8d7da"                            
                    
                    html_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

                    if dismissible_flag == "true":

                        new_value=(
                            '<style>'
                            '.toast-header_' + html_id +' { background-color: ' + background_color + '; display: flex; justify-content: space-between; align-items: center; width: 100%; font-weight: 600;  font-size: 0.95rem; color: #212529;  padding: 1.0rem 1.5rem; margin-bottom: 0px; border: 0px solid transparent; border-radius: 0.1rem;}'
                            '.toast-close_' + html_id + ' { background: none;  border: none;  font-size: 1.2rem;  color: #6c757d;  cursor: pointer;  margin-left: 1rem;}'
                            '.toast-body_' + html_id + ' { background-color: ' + background_color + ';text-align: left;  font-size: 0.875rem;  color: #495057; padding: 0.5rem 1.5rem 1.2rem; margin-bottom: 1rem; border: 1px solid transparent; border-radius: 0.1rem;}'
                            '</style>'
                            '<div class="toast_' + html_id + '"><div class="toast-header_' + html_id + '"><span>' + title_text + '</span><button class="toast-close_' + html_id + '" onclick="this.closest(\'.toast_' + html_id + '\').style.display=\'none\'">&times;</button></div><div class="toast-body_' + html_id +'">' + content + '</div></div>'
                        )

                    else:

                        new_value=(
                            '<style>'
                            '.toast-header_' + html_id +' { background-color: ' + background_color + '; display: flex; justify-content: space-between; align-items: center; width: 100%; font-weight: 600;  font-size: 0.95rem; color: #212529;  padding: 1rem 1.5rem; margin-bottom: 0rem; border: 1px solid transparent; border-radius: 0.375rem;}'
                            '.toast-close_' + html_id + ' { background: none;  border: none;  font-size: 1.2rem;  color: #6c757d;  cursor: pointer;  margin-left: 1rem;}'
                            '.toast-body_' +
                             html_id + ' { background-color: ' + background_color + ';text-align: left;  font-size: 0.875rem;  color: #495057; padding: 1.2rem 1.5rem; margin-bottom: 1rem; border: 1px solid transparent; border-radius: 0.375rem;}'
                            '</style>'
                            '<div class="toast_' + html_id + '"><div class="toast-header_' + html_id + '"><span>' + title_text + '</span></div><div class="toast-body_' + html_id +'">' + content + '</div></div>'
                        )


                    markdown = markdown.replace(key, new_value) 
                    
                # ------------------------------------------------------------------------------            
                # Bootstrap Modal (Micromodal)
                # ------------------------------------------------------------------------------                      

                case "[modal":

                    html_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

                    # Default Values setzen, falls nicht in Settings
                    the_trigger = "OPEN MODAL"
                    the_trigger_text_color = "blue"
                    the_trigger_font_weight = "bold"
                    the_title = "MODAL TITLE"
                    the_text = "Lorem ipsum dolor sit amet consectetur adipisicing elit. Vel, voluptatum. Magni hic, voluptate debitis esse corporis dolor laudantium quae quo!"
                    the_padding = "30px"
                    the_max_width = "500px"
                    the_button_text = "Close the Window"
                    the_space_title_content = "2rem"
                    the_space_content_bottom = "2rem"

                    for subkey, subvalue in value.items():


                        if subkey == "trigger":
                            the_trigger = subvalue
                        if subkey == "content":
                            the_text = subvalue
                        if subkey == "title":
                            the_title = subvalue
                        if subkey == "padding":
                            the_padding = subvalue
                        if subkey == "max_width":
                            the_max_width = subvalue
                        if subkey == "button_text":
                            the_button_text = subvalue
                        if subkey == "space_title_content":
                            the_space_title_content = subvalue
                        if subkey == "space_content_bottom":
                            the_space_content_bottom = subvalue
                        if subkey == "trigger_text_color":
                            the_trigger_text_color = subvalue
                        if subkey == "trigger_font_weight":
                            the_trigger_font_weight = subvalue

                    new_value = ('<style>'
                    '.modal_' + html_id + ' {  font-family: -apple-system,BlinkMacSystemFont,avenir next,avenir,helvetica neue,helvetica,ubuntu,roboto,noto,segoe ui,arial,sans-serif;}'
                    '.modal_trigger {color: ' + the_trigger_text_color + '; background-color: lavender; font-weight: ' + the_trigger_font_weight + ';cursor: pointer; line-height: 1.5; padding: 4px 8px;}'
                    '.modal__overlay_' + html_id + ' {  position: fixed;  top: 0;  left: 0;  right: 0;  bottom: 0;  background: rgba(0,0,0,0.6);  display: flex;  justify-content: center;  align-items: center;}'
                    '.modal__container_' + html_id + ' { background-color: #fff;  padding: ' + the_padding + ';  max-width: ' + the_max_width +';  max-height: 100vh;  border-radius: 4px;  overflow-y: auto;  box-sizing: border-box;}'
                    '.modal__header_' + html_id +' {  display: flex;  justify-content: space-between;  align-items: center;}'
                    '.modal__title_' + html_id + ' {  margin-top: 0;  margin-bottom: 0;  font-weight: 600;  font-size: 1.25rem;  line-height: 1.25;  color: #00449e;  box-sizing: border-box;}'
                    '.modal__close_' + html_id + ' {background: transparent;  border: 0;}'
                    '.modal__header_' + html_id + ' .modal__close_' + html_id + ':before { content: "\\2715"; }'
                    '.modal__content_' + html_id + ' {  margin-top: ' + the_space_title_content +';  margin-bottom: ' + the_space_content_bottom + ';  line-height: 1.5;  color: rgba(0,0,0,.8);}'
                    '.modal__btn_' + html_id + ' {  font-size: .875rem;  padding-left: 1rem;  padding-right: 1rem;  padding-top: .5rem;  padding-bottom: .5rem;  background-color: #e6e6e6;  color: rgba(0,0,0,.8);  border-radius: .25rem;  border-style: none;  border-width: 0;  cursor: pointer;  -webkit-appearance: button;  text-transform: none;  overflow: visible;  line-height: 1.15;  margin: 0;  will-change: transform;  -moz-osx-font-smoothing: grayscale;  -webkit-backface-visibility: hidden;  backface-visibility: hidden;  -webkit-transform: translateZ(0);  transform: translateZ(0);  transition: -webkit-transform .25s ease-out;  transition: transform .25s ease-out;  transition: transform .25s ease-out,-webkit-transform .25s ease-out;}'
                    '.modal__btn_' + html_id + ':focus, .modal__btn:hover {  -webkit-transform: scale(1.05);  transform: scale(1.05);}'
                    '.modal__btn-primary_' + html_id + ' {  background-color: #00449e;  color: #fff;}'
                    '@keyframes mmfadeIn {    from { opacity: 0; }      to { opacity: 1; }}'
                    '@keyframes mmfadeOut {    from { opacity: 1; }      to { opacity: 0; }}'
                    '@keyframes mmslideIn {  from { transform: translateY(15%); }    to { transform: translateY(0); }}'
                    '@keyframes mmslideOut {    from { transform: translateY(0); }    to { transform: translateY(-10%); }}'
                    '.micromodal-slide_' + html_id + ' {  display: none;}'
                    '.micromodal-slide_' + html_id +'.is-open {  display: block;}'       
                    '.micromodal-slide_' + html_id + '[aria-hidden="false"] .modal__overlay_' + html_id + ' {  animation: mmfadeIn .3s cubic-bezier(0.0, 0.0, 0.2, 1);}'
                    '.micromodal-slide_' + html_id + '[aria-hidden="false"] .modal__container_' + html_id + ' {  animation: mmslideIn .3s cubic-bezier(0, 0, .2, 1);}'
                    '.micromodal-slide_' + html_id + '[aria-hidden="true"] .modal__overlay_' +  html_id + ' {  animation: mmfadeOut .3s cubic-bezier(0.0, 0.0, 0.2, 1);}'
                    '.micromodal-slide_' + html_id + '[aria-hidden="true"] .modal__container_' + html_id + ' {  animation: mmslideOut .3s cubic-bezier(0, 0, .2, 1);}'
                    '.micromodal-slide_' + html_id + ' .modal__container_' + html_id + ',.micromodal-slide_' + html_id + ' .modal__overlay_' +  html_id + ' {  will-change: transform;}'
                    '</style>'
                    '<span class="modal_trigger" onclick="MicroModal.show(\'modal-1_' + html_id + '\')">' + the_trigger + '</span>'
                    '<div class="modal micromodal-slide_' + html_id + '" id="modal-1_' + html_id + '" aria-hidden="true">'
                    '<div class="modal__overlay_' + html_id + '" tabindex="-1" data-micromodal-close>'
                    '<div class="modal__container_' + html_id + '"  role="dialog" aria-modal="true" aria-labelledby="modal-1_' + html_id + '-title">'
                    '<header class="modal__header_' + html_id +'">'
                    '<h2 class="modal__title" id="modal-1' + html_id + '-title">' + the_title + '</h2>'          
                    #'<button class="modal__close_' + html_id + '" aria-label="Close modal" data-micromodal-close></button>'
                    '</header>'
                    '<main class="modal__content_' + html_id + '" id="modal-1_' + html_id + '-content">'
                    '<p>' + the_text + '</p'           
                    '</main>'
                    '<footer class="modal__footer_' + html_id + '">'                    
                    '<button class="modal__btn_' +  html_id +'" data-micromodal-close aria-label="' + the_button_text + '">' + the_button_text + '</button>'
                    '</footer>'
                    '</div>'
                    '</div>'
                    '</div>')
                    markdown = markdown.replace(key, new_value)  

                # ------------------------------------------------------------------------------                                
                # DEFAULT Badges
                # ------------------------------------------------------------------------------            
                case "[badge":

                    # Default Values
                    the_background_color = "red"
                    the_text_color = "white"
                    badge_text = "Achtung"
		
                # Values auslesen
                    for subkey, subvalue in value.items():
                        if subkey == "background-color":
                            the_background_color = subvalue
                        if subkey == "text-color":
                            the_text_color = subvalue
                        if subkey == "text":
                            badge_text = subvalue

                    html_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

                    new_value = "<span id = " + html_id + " style='background-color: " + the_background_color + "; color: " + the_text_color + "; padding: 4px 8px; text-align: center; border-radius: 5px;'>" + badge_text + "</span>"
                    
                    markdown = markdown.replace(key, new_value)     


                # ------------------------------------------------------------------------------                                
                # NEWSTICKER
                # ------------------------------------------------------------------------------            
                case "[news_":

                    # Default Values
                    the_background_color = "darkgrey"
                    the_text_color = "white"
                    news_text = "Achtung"
                    text_speed = "20s"
                    the_font_weight = "bold"
        
                    # Values auslesen
                    for subkey, subvalue in value.items():
                        if subkey == "background_color":
                            the_background_color = subvalue
                        if subkey == "text_color":
                            the_text_color = subvalue
                        if subkey == "text":
                            news_text = subvalue
                        if subkey == "font_weight":
                            the_font_weight = subvalue
                        if subkey == "speed":
                            text_speed = subvalue


                    html_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

                    new_value = (
                        '<style>'
                        '.newsticker-container_' + html_id + '{ overflow: hidden;  white-space: nowrap;  width: 100%; border: 1px solid #ccc;  background: ' + the_background_color + ';  padding: 5px 0;  font-family: sans-serif;}'
                        '.newsticker_' + html_id + ' { display: inline-block;  padding-left: 100%;  animation: ticker ' + text_speed + 's linear infinite; color: ' + the_text_color + '; font-weight: ' + the_font_weight +';}'
                        '@keyframes ticker {  0%   { transform: translateX(0); }  100% { transform: translateX(-100%); }}'
                        '</style>'
                        '<div class="newsticker-container_' + html_id + '"><div class="newsticker_' + html_id + '"><span>' + news_text + '</span>'
                        '</div></div>'                      
                        )
                    
                    markdown = markdown.replace(key, new_value)         
                    
                # ------------------------------------------------------------------------------                                
                # MASTODON
                # ------------------------------------------------------------------------------ 
                case "[masto":
                    
                    # Define default values
                    the_class_name_date = "default_rss_date"
                    the_class_name_content = "default_rss_content"
                    the_class_name_link = "default_rss_link"

                    for subkey, subvalue in value.items():
                        if subkey == "mastodon_username":
                            the_username = subvalue
                            the_feed_url = "https://mastodon.social/users/" + the_username + ".rss"
                        if subkey == "mastodon_class_date":
                            the_class_name_date = subvalue
                        if subkey == "mastodon_class_content":
                            the_class_name_content = subvalue
                        if subkey == "mastodon_class_link":
                            the_class_name_link = subvalue
                            
                    feed = feedparser.parse(the_feed_url)  

                    latest_entry = feed.entries[0]  # Der aktuellste Eintrag                          

                    # Versuche zuerst den Titel, dann die Zusammenfassung, dann den Inhalt
                    title = getattr(latest_entry, 'title', None)
                    if not title:
                        title = getattr(latest_entry, 'summary', None)
                    if not title and 'content' in latest_entry:
                        title = latest_entry.content[0].value.strip()
                    if not title:
                        title = "[Kein Titel verfügbar]"                               

                    dt = getattr(latest_entry, 'published', None)                            
                    dt_parsed = parsedate_to_datetime(dt)

                    the_date = dt_parsed.strftime("%d. %B %Y, %H:%M Uhr")  # Ausgabe: 09 Okt 25, 20:20

                    the_link = getattr(latest_entry, 'link', None)

                    if len(title) > 0:

                        #self.write_protokoll(title)
                        # Define default styles
                        new_value = ('<style>'
                            '.default_rss_date {font-size: 13px; font-weight: bold; color: blue; margin-bottom: 10px; display: block; margin-left: 20px; text-align: right;}'
                            '.default_rss_content {font-size: 14px; font-weight: bold; margin-bottom: 10px; display: block; margin-left: 20px; }'
                            '.default_rss_link {font-size: 11px; font-weight: normal; margin-bottom: 10px; display: block; margin-left: 20px;}'
                            '</style>'
                            )                        
                        title = title.replace("<p>","")
                        title = title.replace("</p>","")
                        title = title.replace("'", "")
                        title = title.replace("\"", "")
                        title = title.replace("&quot;", "\"")

                        new_value = new_value.replace("'","")
                        new_value = new_value + "<span class='" + the_class_name_date + "'>" + the_date + "</span><span class='" + the_class_name_content + "'>" + title + "</span><span class='" + the_class_name_link + "'><a href='" + the_link + "'>Link zum Originalpost</a> | MASTODON KANAL: <a href='https://mastodon.social/@" + the_username + "' target='_blank'>" + the_username + "</a><span>"
                
                    markdown = markdown.replace(key, new_value)   

                # ------------------------------------------------------------------------------                                
                # DATE & Time Replacement
                # ------------------------------------------------------------------------------            

                case "[date_":                    
                    
                    # Default Values                    
                    the_date_format = "red"                    
		
                    # Values auslesen
                    for subkey, subvalue in value.items():
                        if subkey == "date_format":
                            the_date_format = subvalue   
                            
                    # Datum formatieren    
                    jetzt = datetime.now()
                    new_Date = jetzt.strftime(the_date_format)                                             

                    html_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

                    new_value = "<span id = " + html_id + ">" + new_Date + "</span>"
                    
                    markdown = markdown.replace(key, new_value)    
                    
                # ------------------------------------------------------------------------------                                
                # DEFAULT Replacement
                # ------------------------------------------------------------------------------            
                case _:
                    #log.debug("Return Value DEFAULT  : " + value)                 
                    markdown = markdown.replace(key, value)   
                    #return markdown
        return markdown
            
            
        