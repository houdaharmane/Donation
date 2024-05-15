from flask import Flask, render_template, request , jsonify 
import stripe
import logging 
import database_module
import mysql.connector
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from flask import send_file
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import os
from datetime import datetime
from reportlab.platypus import Image

try:
    myconn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="estsb",
        database="donation"
    )
    if myconn.is_connected():
        print("Connexion à la base de données établie avec succès.")
    else:
        print("La connexion à la base de données a échoué.")
except mysql.connector.Error as err:
    print("Erreur lors de la connexion à la base de données MySQL :", err)


app = Flask(__name__)
app.template_folder = 'C:/Users/hp/Documents/My project (stage technique)'

@app.route('/')
def accueil():
    data = {
        'titre': "Bienvenue à l'application de gestion des dons",
        'description': "Aidez les victimes du séisme d'El Haouz en faisant un don."
    }
    return render_template('acceuil.html', data=data)

@app.route('/Our team.html')
def Ourteam():
    data = {
        'titre': "Bienvenue à l'application de gestion des dons",
        'description': "Aidez les victimes du séisme d'El Haouz en faisant un don."
    }
    return render_template('Our team.html', data=data)

@app.route('/about.html')
def about():
    data = {
        'titre': "À propos de nous",
        'description': "En savoir plus sur notre mission et notre engagement."
    }
    return render_template('about.html', data=data)

@app.route('/donation.html', methods=['GET', 'POST'])
def donation():
    if request.method == 'POST':
        # Récupérer le montant du formulaire de donation
        montant = request.form['montant']
        # Créer la session de paiement avec Stripe
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': 'Don',
                    },
                    'unit_amount': int(montant) * 100,  
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.url_root + 'merci.html',
            cancel_url=request.url_root + 'annuler.html',
        )
        
        return render_template('paiement.html', session_id=session.id)
    
    data = {
        'titre': "Faire un Don",
        'description': "Faites un don pour soutenir les personnes dans le besoin."
    }
    return render_template('donation.html', data=data)

@app.route('/contact.html')
def contact():
    data = {
        'titre': "Contactez-nous",
        'description': "Pour toute question ou requête, n'hésitez pas à nous contacter."
    }
    return render_template('contact.html', data=data)

@app.route('/verify_donation')
def verify_donation():
    user_id = request.args.get('user_id')  # ID de l'utilisateur que vous souhaitez vérifier
    donation_amount = 1000  # Montant du don à vérifier (1000 centimes = 10 euros)

    # Vérifiez dans la base de données si l'utilisateur a effectué un don du montant spécifique
    donation_exists = database_module.check_donation(user_id, donation_amount)

    if donation_exists:
        return render_template('donation_verified.html')
    else:
        return render_template('donation_not_verified.html')

@app.route('/index')
def index():
    cursor = myconn.cursor()
    cursor.execute("SELECT * FROM contact_info")
    result = cursor.fetchall()
    return str(result)

@app.route('/envoyer_donnees', methods=['POST'])
def envoyer_donnees():
    if request.method == 'POST':
        nom = request.form.get('name')
        email = request.form.get('email')
        numero_telephone = request.form.get('number')
        message = request.form.get('message')

        if nom and email and numero_telephone and message:
            cursor = myconn.cursor()
            # Insérer les données dans la table contact_info
            cursor.execute("INSERT INTO contact_info (name, email, number, message) VALUES (%s, %s, %s, %s)", (nom, email, numero_telephone, message))
            myconn.commit()

            # Maintenant, insérez également ces données dans la table de la facture
            cursor.execute("INSERT INTO facture (name, email, number) VALUES (%s, %s, %s)", (nom, email, numero_telephone))
            myconn.commit()

            cursor.close()
            myconn.close()

            return render_template('donation_success.html')
        else:
            return render_template('donation_error.html')
    else:
        return "Erreur lors de l'envoi des données."
# Route pour le formulaire de donation
@app.route('/get_montants')
def get_montants():
    # Utilisez la connexion à la base de données pour récupérer les montants de la table "donation"
    cursor = myconn.cursor()
    cursor.execute("SELECT * FROM donation")
    result = cursor.fetchall()

    # Fermez le curseur après avoir récupéré les données
    cursor.close()
    return jsonify({'montants': result})


@app.route('/enregistrer_montant', methods=['POST'])
def enregistrer_montant():
    if request.method == 'POST':
        montant = request.form.get('montant')
        if montant:
            method = request.form.get('method')
            cursor = myconn.cursor()
            cursor.execute("INSERT INTO donation (montant, method) VALUES (%s, %s)", (montant, method))
            myconn.commit()

            # Maintenant, enregistrez également ces données dans la table de la facture
            name = request.form.get('name')
            email = request.form.get('email')
            number = request.form.get('number')
            cursor.execute("INSERT INTO facture (name, email, number, montant) VALUES (%s, %s, %s, %s)", (name, email, number, montant))
            myconn.commit()

            cursor.close()

            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Le montant est vide.'})
    else:
        return jsonify({'success': False, 'message': 'Méthode non autorisée.'})

    
@app.route('/charge', methods=['POST'])
def charge():
    if request.method == 'POST':
        prenom = request.form.get('prenom')
        nom = request.form.get('nom')
        email = request.form.get('email')
        destinataire = request.form.get('destinataire')
        montant = request.form.get('montant')
        compte_source = request.form.get('compte_source')
        mot_de_passe = request.form.get('mot_de_passe')

        print("Prenom :", prenom)
        print("Nom :", nom)
        print("Email :", email)
        print("Destinataire :", destinataire)
        print("Montant :", montant)
        print("Compte Source :", compte_source)
        print("Mot de Passe :", mot_de_passe)

        try:
            cursor = myconn.cursor()
            # Assurez-vous d'avoir les colonnes nécessaires dans votre table "donation"
            cursor.execute("INSERT INTO donation (prenom, nom, email, destinataire, montant, compte_source, mot_de_passe) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                           (prenom, nom, email, destinataire, montant, compte_source, mot_de_passe))
            print("Requête SQL :", cursor.statement) 
            myconn.commit()
            cursor.close()

            return render_template('donation_success.html', message="Le don a été enregistré avec succès.")
    
        except mysql.connector.Error as err:
            print("Erreur MySQL :", err)
            return jsonify({'success': False, 'message': 'Erreur MySQL lors de l\'insertion dans la base de données.'})

    else:
        return jsonify({'success': False, 'message': 'Méthode non autorisée.'})

@app.route('/confirmer', methods=['POST'])
def confirmer():
    try:
        proprietaire = request.form['proprietaire']
        cvv = request.form['cvv']
        numero_carte = request.form['numero_carte']
        date_expiration_month = request.form.get('date_expiration_month')
        date_expiration_year = request.form.get('date_expiration_year')
        
        cursor = myconn.cursor()
        cursor.execute('INSERT INTO donation (proprietaire, cvv, numero_carte, date_expiration_month, date_expiration_year) VALUES (%s, %s, %s, %s, %s)', (proprietaire, cvv, numero_carte, date_expiration_month, date_expiration_year))
        myconn.commit()
        cursor.close()

        return render_template('donation_success.html', message="Le don a été enregistré avec succès.")

    except mysql.connector.Error as err:
        logging.error(f"Erreur MySQL : {err}")
        return render_template('donation_error.html', error=f"Erreur MySQL : {err.msg}")
    
   # Créer un document PDF 
def generate_invoice_pdf(nom, email, numero_telephone, montant, filename='invoice.pdf'):
    doc = SimpleDocTemplate(filename, pagesize=letter)
    
    # Définir un style pour le titre
    title_style = ParagraphStyle(
        name='TitleStyle',
        fontSize=20,
        textColor=colors.blue,
        leading=30
    )

    # Définir un style pour le contenu
    content_style = ParagraphStyle(
        name='ContentStyle',
        fontSize=12,
        leading=15
    )

    # Contenu de la facture
    content = []

    # Insérer l'image en haut de la facture
    logo_path = "https://tse1.mm.bing.net/th?id=OIP.3ybAshMFHGjkSlmM-0X4qAHaDV&pid=Api&P=0&h=180"
    logo = Image(logo_path, width=300, height=100)
    content.append(logo)

    content.append(Paragraph("Votre facture", title_style))
    content.append(Paragraph("Nom: {}".format(nom), content_style))
    content.append(Paragraph("Email: {}".format(email), content_style))
    content.append(Paragraph("Numéro de téléphone: {}".format(numero_telephone), content_style))
    content.append(Paragraph("Montant: {}".format(montant), content_style))

    # Ajouter les détails supplémentaires à la facture
    content.append(Paragraph("Résumé", title_style))
    content.append(Paragraph("Remerciements aux donateurs", content_style))
    content.append(Paragraph("Nous tenons à exprimer notre profonde gratitude à tous nos donateurs pour leur générosité et leur soutien précieux.", content_style))

    # Ajouter la date actuelle à la facture
    date_actuelle = datetime.now().strftime("%d/%m/%Y %I:%M %p")
    content.append(Paragraph("Date: {}".format(date_actuelle), content_style))

    # Ajouter l'adresse et les informations de contact
    content.append(Paragraph("Besoin d'aide?", title_style))
    content.append(Paragraph("123 Avenue Mohammed V, Casablanca, Maroc.", content_style))
    content.append(Paragraph("INFORMATIONS DE CONTACT: donationclub199@gmail.com", content_style))

    # Ajouter le contenu au document PDF
    doc.build(content)

    return filename

@app.route('/send_invoice', methods=['POST'])
def send_invoice():
    if request.method == 'POST':
        nom = request.form.get('nom')
        email = request.form.get('email')
        numero_telephone = request.form.get('numero')
        montant = request.form.get('montant')

        if nom and email and numero_telephone and montant:
            # Insérer les données dans la base de données
            cursor = myconn.cursor()
            cursor.execute("INSERT INTO facture (name, email, number, montant) VALUES (%s, %s, %s, %s)", (nom, email, numero_telephone, montant))
            myconn.commit()
            cursor.close()

            # Générer le fichier PDF de la facture
            pdf_path = generate_invoice_pdf(nom, email, numero_telephone, montant)

            # Vérifiez si le chemin du fichier PDF est valide
            if pdf_path:
                # Envoyer le fichier PDF en tant que réponse à la requête
                return send_file(pdf_path, as_attachment=True)
            else:
                return render_template('donation_error.html', message="Erreur lors de la génération du fichier PDF de la facture.")
        else:
            # Retourner une réponse indiquant qu'il manque des informations dans le formulaire
            return render_template('donation_error.html', message="Veuillez remplir tous les champs du formulaire.")
        
        
        
@app.route('/getfacture')
def getfacture():
    # Récupérer les informations de la dernière facture depuis la base de données
    cursor = myconn.cursor()
    cursor.execute("SELECT name, email, number, montant FROM facture ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()
    myconn.commit()
    cursor.close()

    # Si des données sont trouvées dans la base de données
    if result:
        name, email, number, montant = result
        print("Données de la facture récupérées avec succès :", name, email, number, montant)  # Ajoutez cette ligne pour le débogage
        data = {
        "name": "John Doe",
        "email": "johndoe@example.com",
        "number": "123456789",
        "montant": "$50"
    }
        return render_template('Our team.html', data=data)  # Assurez-vous que le modèle HTML s'appelle 'Our team.html'
    else:
        print("Aucune donnée de facture n'a été trouvée dans la base de données.") 
        return "Aucune donnée de facture n'a été trouvée dans la base de données."


if __name__ == '__main__':
    app.run(debug=True)
