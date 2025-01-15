import pandas as pd
import csv
import os
import hashlib
import requests
import random
import string
import smtplib
import datetime

# Fichiers CSV pour stocker les données
comptes_csv = "comptes.csv"
produits_csv = "produits.csv"
logs_csv = "logs.csv"

# Fonction pour initialiser les fichiers CSV si nécessaire
def initialiser_fichiers():
    if not os.path.exists(comptes_csv):
        with open(comptes_csv, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["id", "nom", "mot_de_passe", "salt", "email"])

    if not os.path.exists(produits_csv):
        pd.DataFrame(columns=["utilisateur_id", "nom", "prix", "quantite"]).to_csv(produits_csv, index=False)

    if not os.path.exists(logs_csv):
        with open(logs_csv, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Date", "Logs"])

def enregistrer_log(nom_utilisateur, succes):
    date_heure = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result = "Succès" if succes else "Échec"

    with open(logs_csv, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([date_heure, f"Connexion de {nom_utilisateur}: {result}"]) #ajouter si le mdp est compromis ou non / 

def creer_compte():
    """
    Crée un nouveau compte utilisateur avec un mot de passe haché et un sel.
    """
    initialiser_fichiers()
    nom = input("Entrez votre nom : ")
    mot_de_passe = input("Entrez votre mot de passe : ")
    email = input("Entrez une adresse mail : ")

    # Vérifier si le mot de passe est dans rockyou.txt ou via HIBP
    if verifier_rockyou(mot_de_passe):
        print("Le mot de passe est trop courant (rockyou.txt). Veuillez choisir un mot de passe plus sécurisé.")
        return

    if verifier_hibp(mot_de_passe):
        print("Le mot de passe a été compromis (Have I Been Pwned). Veuillez choisir un mot de passe plus sécurisé.")
        return

    # Générer un sel aléatoire
    salt = ''.join(random.choices(string.ascii_letters + string.digits, k=6))

    # Hacher le mot de passe avec le sel
    mot_de_passe_hash = hashlib.sha256((mot_de_passe + salt).encode('utf-8')).hexdigest()

    # Récupérer l'ID utilisateur
    with open(comptes_csv, mode="r") as file:
        reader = csv.reader(file)
        next(reader)
        id_utilisateur = int(sum(1 for row in reader)) + 1

    # Ajouter l'utilisateur au fichier
    with open(comptes_csv, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([id_utilisateur, nom, mot_de_passe_hash, salt, email])

    print("Compte créé avec succès !")

def verifier_identifiants(nom, mot_de_passe):
    """
    Vérifie les identifiants en comparant le hash du mot de passe fourni avec celui stocké.
    """
    initialiser_fichiers()

    with open(comptes_csv, mode="r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["nom"] == nom:
                # Récupérer le sel et vérifier le hash
                salt = row["salt"]
                hash_a_verifier = hashlib.sha256((mot_de_passe + salt).encode('utf-8')).hexdigest()
                if hash_a_verifier == row["mot_de_passe"]:
                    enregistrer_log(nom, succes=True)
                    return int(row["id"])
    enregistrer_log(nom, succes=False)
    return None

def ajouter_produit(utilisateur_id):
    nom = input("Entrez le nom du produit : ")
    prix = float(input("Entrez le prix du produit : "))
    quantite = int(input("Entrez la quantité : "))

    df = pd.read_csv(produits_csv)
    df = pd.concat([df, pd.DataFrame([[utilisateur_id, nom, prix, quantite]], columns=["utilisateur_id", "nom", "prix", "quantite"])], ignore_index=True)
    df.to_csv(produits_csv, index=False)

    print("Produit ajouté avec succès !")

def supprimer_produit(utilisateur_id):
    nom = input("Entrez le nom du produit à supprimer : ")

    df = pd.read_csv(produits_csv)
    df_user = df[df["utilisateur_id"] == utilisateur_id]
    if nom in df_user["nom"].values:
        df = df[~((df["utilisateur_id"] == utilisateur_id) & (df["nom"] == nom))]
        df.to_csv(produits_csv, index=False)
        print("Produit supprimé avec succès !")
    else:
        print("Produit introuvable.")

def afficher_produits(utilisateur_id):
    df = pd.read_csv(produits_csv)
    df_user = df[df["utilisateur_id"] == utilisateur_id]
    if df_user.empty:
        print("Aucun produit disponible.")
    else:
        print("\nListe des produits :")
        print(df_user)

def rechercher_produit_sequentielle(utilisateur_id):
    try:
        nom_produit = input("Quel est le nom du produit recherché ? : ").strip()

        df = pd.read_csv(produits_csv)
        df_user = df[(df["utilisateur_id"] == utilisateur_id) & (df["nom"].str.strip().str.lower() == nom_produit.lower())]

        if not df_user.empty:
            for _, row in df_user.iterrows():
                print(f"Produit trouvé : {row['nom']}, Quantité : {row['quantite']}, Prix : {row['prix']} euro(s)")
        else:
            print(f"Le produit '{nom_produit}' n'a pas été trouvé.")
    except Exception as e:
        print(f"Une erreur s'est produite : {e}")

def modifier_mot_de_passe(utilisateur_id):
    try:
        with open(comptes_csv, mode="r") as file:
            comptes = list(csv.DictReader(file))
    except FileNotFoundError:
        print("Erreur : fichier des comptes introuvable.")
        return

    utilisateur = next((u for u in comptes if int(u["id"]) == utilisateur_id), None)
    if not utilisateur:
        print("Utilisateur introuvable.")
        return

    ancien_mdp = input("Entrez votre ancien mot de passe : ")
    ancien_mdp_hash = hashlib.sha256((ancien_mdp + utilisateur["salt"]).encode("utf-8")).hexdigest()

    if ancien_mdp_hash != utilisateur["mot_de_passe"]:
        print("L'ancien mot de passe est incorrect.")
        return

    nouveau_mdp = input("Entrez votre nouveau mot de passe : ")
    confirmation_mdp = input("Confirmez votre nouveau mot de passe : ")

    if nouveau_mdp != confirmation_mdp:
        print("Les mots de passe ne correspondent pas.")
        return

    if verifier_rockyou(nouveau_mdp):
        print("Le nouveau mot de passe est trop courant (rockyou.txt). Veuillez en choisir un autre.")
        return

    if verifier_hibp(nouveau_mdp):
        print("Le nouveau mot de passe a été compromis (Have I Been Pwned). Veuillez en choisir un autre.")
        return

    utilisateur["mot_de_passe"] = hashlib.sha256((nouveau_mdp + utilisateur["salt"]).encode("utf-8")).hexdigest()

    with open(comptes_csv, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["id", "nom", "mot_de_passe", "salt", "email"])
        writer.writeheader()
        writer.writerows(comptes)

    print("Mot de passe modifié avec succès !")

def verifier_rockyou(mot_de_passe):
    mot_de_passe_hash = hashlib.sha256(mot_de_passe.encode('utf-8')).hexdigest()
    try:
        with open("rockyou_hashed.txt", "r") as file:
            for line in file:
                if mot_de_passe_hash == line.strip():
                    return True
        return False
    except FileNotFoundError:
        print("Erreur : le fichier rockyou_hashed.txt est introuvable.")
        return False

def verifier_hibp(mot_de_passe):
    sha1_hash = hashlib.sha1(mot_de_passe.encode("utf-8")).hexdigest().upper()
    prefix = sha1_hash[:5]
    suffix = sha1_hash[5:]

    url = f"https://api.pwnedpasswords.com/range/{prefix}"
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Erreur lors de l'accès à l'API HIBP : {response.status_code}")
            return False

        hashes = response.text.splitlines()
        for h in hashes:
            hash_suffix, count = h.split(":")
            if hash_suffix == suffix:
                print(f"Mot de passe compromis ! Trouvé {count} fois dans les bases de données compromises.")
                return True
        return False
    except requests.RequestException as e:
        print(f"Erreur réseau : {e}")
        return False

def menu_principal():
    initialiser_fichiers()

    while True:
        print("\n=== Menu Principal ===")
        print("1. Créer un compte")
        print("2. Se connecter")
        print("3. Quitter")

        choix = input("Votre choix : ")

        if choix == "1":
            creer_compte()
        elif choix == "2":
            nom = input("Entrez votre nom : ")
            mot_de_passe = input("Entrez votre mot de passe : ")

            utilisateur_id = verifier_identifiants(nom, mot_de_passe)
            if utilisateur_id:
                print("Connexion réussie !")
                menu_gestion(utilisateur_id)
            else:
                print("Identifiants incorrects.")
        elif choix == "3":
            print("Au revoir !")
            break
        else:
            print("Choix invalide, veuillez réessayer.")

def menu_gestion(utilisateur_id):
    while True:
        print("\n=== Menu Gestion des Produits ===")
        print("1. Ajouter un produit")
        print("2. Supprimer un produit")
        print("3. Afficher les produits")
        print("4. Rechercher un produit")
        print("5. Modifier le mot de passe")
        print("6. Quitter")

        choix = input("Votre choix : ")

        if choix == "1":
            ajouter_produit(utilisateur_id)
        elif choix == "2":
            supprimer_produit(utilisateur_id)
        elif choix == "3":
            afficher_produits(utilisateur_id)
        elif choix == "4":
            rechercher_produit_sequentielle(utilisateur_id)
        elif choix == "5":
            modifier_mot_de_passe(utilisateur_id)
        elif choix == "6":
            print("Déconnexion...\n")
            break
        else:
            print("Choix invalide, veuillez réessayer.")

# Lancer le menu principal
menu_principal()
