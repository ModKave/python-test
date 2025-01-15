import tkinter as tk
import os
import csv
from tkinter import ttk, messagebox
from main import afficher, ajouter, recherche_produit, supprimer_produit
from modules.fonction import verifier_hibp_password, verifier_complexite, hash_password, charger_rockyou, ajouter_utilisateur, generer_salt, modifier_mot_de_passe, compromis_rockyou, envoyer_notification, enregistrer_historique
from datetime import datetime

utilisateur_fichier = None
EMAIL_NOTIFICATION = "abequet@guardiaschool.fr"

def verifier_et_securiser_mdp(email, mot_de_passe):
    """Vérifie et sécurise un mot de passe avant l'enregistrement."""
    rockyou_file = "rockyou.csv"
    rockyoucsv = charger_rockyou(rockyou_file)

    if compromis_rockyou(mot_de_passe, rockyoucsv):
        envoyer_notification(EMAIL_NOTIFICATION, email, "RockYou")
        messagebox.showwarning("Mot de passe compromis", 
                               "Votre mot de passe est compromis (base RockYou). Veuillez en choisir un autre.")
    

    if verifier_hibp_password(mot_de_passe):
        envoyer_notification(EMAIL_NOTIFICATION, email, "HIBP")
        messagebox.showwarning("Mot de passe compromis", 
                               "Votre mot de passe est compromis (base HIBP). Veuillez en choisir un autre.")
        return False

    complexite_erreur = verifier_complexite(mot_de_passe)
    if complexite_erreur:
        messagebox.showwarning("Complexité insuffisante", 
                               "Votre mot de passe ne respecte pas les critères de complexité.")
        return False

    return True

def connexion_utilisateur(login, mdp):
    """Vérifie les identifiants d'un utilisateur existant."""

    try:
        if mdp == "" or login == "":
            enregistrer_historique(
                login=login,
                connexion="Interface graphique",
                statut_connexion="Échec : Identifiants manquants",
                compromis=False,
                date=datetime.now()
            )
            return None

        if os.path.exists("utilisateurs.csv"):
            with open("utilisateurs.csv", mode="r", newline="", encoding="utf-8") as fichier:
                reader = csv.DictReader(fichier)
                for ligne in reader:
                    if ligne["email"] == login:
                        hashed_mdp = hash_password(mdp, ligne["salt"])
                        if hashed_mdp == ligne["mdp"]:
                            enregistrer_historique(
                                login=login,
                                connexion="Interface graphique",
                                statut_connexion="Connexion réussie",
                                compromis=False,
                                date=datetime.now()
                            )
                            return login

                        enregistrer_historique(
                            login=login,
                            connexion="Interface graphique",
                            statut_connexion="Échec : Mot de passe incorrect",
                            compromis=False,
                            date=datetime.now()
                        )
                        return None

        enregistrer_historique(
            login=login,
            connexion="Interface graphique",
            statut_connexion="Échec : Utilisateur introuvable",
            compromis=False,
            date=datetime.now()
        )
        return None
    except Exception as e:
        print(f"Erreur : {e}")
        enregistrer_historique(
            login=login,
            connexion="Interface graphique",
            statut_connexion=f"Erreur : {e}",
            compromis=False,
            date=datetime.now()
        )
        return None

def trier_colonne(colonne, reverse=False):
    lignes = [(tree_produits.set(k, colonne), k) for k in tree_produits.get_children('')]
    lignes.sort(reverse=reverse, key=lambda x: float(x[0].split()[0]) if colonne != "Produit" else x[0].lower())
    for index, (_, k) in enumerate(lignes):
        tree_produits.move(k, '', index)
    tree_produits.heading(colonne, command=lambda: trier_colonne(colonne, not reverse))

def gestion_interface():
    def afficher_produits():
        for row in tree_produits.get_children():
            tree_produits.delete(row)
        try:
            df = afficher(utilisateur_fichier)
            for _, row in df.iterrows():
                tree_produits.insert("", "end", values=(row['Produit'], row['Prix'], row['Quantité']))
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'afficher les produits : {e}")

    def ajouter_produit():
        produit, prix, quantite = champ_nom.get().strip(), champ_prix.get().strip(), champ_quantite.get().strip()
        if produit and prix.isdigit() and quantite.isdigit():
            try:
                ajouter(utilisateur_fichier, produit, int(prix), int(quantite))
                afficher_produits()
                champ_nom.delete(0, tk.END)
                champ_prix.delete(0, tk.END)
                champ_quantite.delete(0, tk.END)
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible d'ajouter le produit : {e}")
        else:
            messagebox.showwarning("Attention", "Veuillez remplir correctement tous les champs.")

    def rechercher_produit():
        produit = champ_recherche.get().strip()
        if produit:
            resultat = recherche_produit(utilisateur_fichier, produit)
            for row in tree_produits.get_children():
                tree_produits.delete(row)
            for _, row in resultat.iterrows():
                tree_produits.insert("", "end", values=(row['Produit'], row['Prix'], row['Quantité']))
        else:
            messagebox.showwarning("Attention", "Veuillez entrer un nom de produit pour la recherche.")

    def rafraichir():
        afficher_produits()
        champ_recherche.delete(0, tk.END)

    def supprimer_produit_selectionne():
        try:
            item = tree_produits.selection()[0]
            valeurs = tree_produits.item(item, 'values')
            produit = valeurs[0]
            supprimer_produit(utilisateur_fichier, produit)
            afficher_produits()
        except IndexError:
            messagebox.showwarning("Attention", "Veuillez sélectionner un produit à supprimer.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de supprimer le produit : {e}")

    def deconnexion():
        fenetre.destroy()
        connexion_interface()

    fenetre = tk.Tk()
    fenetre.title("Gestion des produits")
    fenetre.geometry("700x600")
    fenetre.iconbitmap("images/bat.ico")

    tk.Label(fenetre, text=f"Bienvenue, {utilisateur_fichier.split('.')[0]}", font=("Times New Roman", 16)).pack(pady=10)

    btn_deconnexion = tk.Button(fenetre, text="Déconnexion", font=("Times New Roman", 12),  command=deconnexion)
    btn_deconnexion.pack(pady=5)

    frame_recherche = tk.Frame(fenetre)
    frame_recherche.pack(pady=10)

    champ_recherche = tk.Entry(frame_recherche)
    champ_recherche.grid(row=0, column=0, padx=5, pady=5)
    btn_recherche = tk.Button(frame_recherche, text="Rechercher", font=("Times New Roman", 12), command=rechercher_produit)
    btn_recherche.grid(row=0, column=1, padx=5, pady=5)
    btn_rafraichir = tk.Button(frame_recherche, text="Rafraîchir", font=("Times New Roman", 12),  command=rafraichir)
    btn_rafraichir.grid(row=0, column=2, padx=5, pady=5)

    frame_ajout = tk.Frame(fenetre)
    frame_ajout.pack(pady=10)

    tk.Label(frame_ajout, text="Nom :", font=("Times New Roman", 12)).grid(row=0, column=0, padx=5, pady=5)
    champ_nom = tk.Entry(frame_ajout)
    champ_nom.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(frame_ajout, text="Prix :", font=("Times New Roman", 12)).grid(row=1, column=0, padx=5, pady=5)
    champ_prix = tk.Entry(frame_ajout)
    champ_prix.grid(row=1, column=1, padx=5, pady=5)

    tk.Label(frame_ajout, text="Quantité :", font=("Times New Roman", 12)).grid(row=2, column=0, padx=5, pady=5)
    champ_quantite = tk.Entry(frame_ajout)
    champ_quantite.grid(row=2, column=1, padx=5, pady=5)

    btn_ajouter = tk.Button(frame_ajout, text="Ajouter produit", command=ajouter_produit, font=("Times New Roman", 12))
    btn_ajouter.grid(row=3, column=0, pady=10)

    btn_supprimer = tk.Button(frame_ajout, text="Supprimer produit", command=supprimer_produit_selectionne, font=("Times New Roman", 12))
    btn_supprimer.grid(row=3, column=2, pady=10)

    columns = ("Produit", "Prix", "Quantité")
    global tree_produits
    tree_produits = ttk.Treeview(fenetre, columns=columns, show="headings")

    for col in columns:
        tree_produits.heading(col, text=col, command=lambda c=col: trier_colonne(c))
        tree_produits.column(col, width=200 if col == "Produit" else 100, anchor="center")

    tree_produits.pack(fill="both", expand=True, pady=10)

    afficher_produits()

    fenetre.mainloop()

def connexion_interface():
    def se_connecter():
        global utilisateur_fichier
        email = champ_email.get().strip()
        mdp = champ_mdp.get().strip()
        if not verifier_et_securiser_mdp(EMAIL_NOTIFICATION, mdp):
            return
        utilisateur = connexion_utilisateur(email, mdp)
        if utilisateur:
            utilisateur_fichier = f"{utilisateur}.csv"
            fenetre_connexion.destroy()
            gestion_interface()
        else:
            messagebox.showerror("Erreur", "E-mail ou mot de passe incorrect.")

    def creer_compte():
        def valider_inscription():
            email = champ_email_inscription.get().strip()
            nom = champ_nom_inscription.get().strip()
            mdp = champ_mdp_inscription.get().strip()
            if verifier_et_securiser_mdp(EMAIL_NOTIFICATION, mdp):
                salt = generer_salt()
                ajouter_utilisateur(email, nom, hash_password(mdp, salt), salt)
                fenetre_inscription.destroy()
                messagebox.showinfo("Succès", "Compte créé avec succès !")

        fenetre_inscription = tk.Toplevel(fenetre_connexion)
        fenetre_inscription.title("Inscription")
        fenetre_inscription.geometry("400x350")
        fenetre_inscription.iconbitmap("images/bat.ico")

        tk.Label(fenetre_inscription, text="Inscription", font=("Times New Roman", 16)).pack(pady=10)

        tk.Label(fenetre_inscription, text="Nom :", font=("Times New Roman", 12)).pack(pady=5)
        champ_nom_inscription = tk.Entry(fenetre_inscription, width=25)
        champ_nom_inscription.pack(pady=5)

        tk.Label(fenetre_inscription, text="E-mail :", font=("Times New Roman", 12)).pack(pady=5)
        champ_email_inscription = tk.Entry(fenetre_inscription, width=25)
        champ_email_inscription.pack(pady=5)

        tk.Label(fenetre_inscription, text="Mot de passe :", font=("Times New Roman", 12)).pack(pady=5)
        champ_mdp_inscription = tk.Entry(fenetre_inscription, show="*", width=25)
        champ_mdp_inscription.pack(pady=5)

        btn_valider = tk.Button(fenetre_inscription, text="Valider", font=("Times New Roman", 12), command=valider_inscription)
        btn_valider.pack(pady=20)

    def modifier_mdp():
        def valider_modification():
            email = champ_email_mdp.get().strip()
            mdp = champ_mdp_modification.get().strip()
            if verifier_et_securiser_mdp(email, mdp):
                salt = generer_salt()
                nouveau_mdp = hash_password(mdp, salt)
                modifier_mot_de_passe(email, nouveau_mdp, salt)
                fenetre_modification.destroy()
                messagebox.showinfo("Succès", "Mot de passe modifié avec succès !")

        fenetre_modification = tk.Toplevel(fenetre_connexion)
        fenetre_modification.title("Modifier mot de passe")
        fenetre_modification.geometry("400x350")
        fenetre_modification.iconbitmap("images/bat.ico")

        tk.Label(fenetre_modification, text="Modification du mot de passe", font=("Times New Roman", 16)).pack(pady=10)

        tk.Label(fenetre_modification, text="E-mail :", font=("Times New Roman", 12)).pack(pady=5)
        champ_email_mdp = tk.Entry(fenetre_modification, width=25)
        champ_email_mdp.pack(pady=5)

        tk.Label(fenetre_modification, text="Nouveau mot de passe :", font=("Times New Roman", 12)).pack(pady=5)
        champ_mdp_modification = tk.Entry(fenetre_modification, show="*", width=25)
        champ_mdp_modification.pack(pady=5)

        btn_valider = tk.Button(fenetre_modification, text="Valider", font=("Times New Roman", 12), command=valider_modification)
        btn_valider.pack(pady=20)

    fenetre_connexion = tk.Tk()
    fenetre_connexion.title("Connexion")
    fenetre_connexion.geometry("400x350")
    fenetre_connexion.iconbitmap("images/bat.ico")

    tk.Label(fenetre_connexion, text="Connexion", font=("Times New Roman", 16)).pack(pady=10)

    tk.Label(fenetre_connexion, text="E-mail :", font=("Times New Roman", 12)).pack(pady=5)
    champ_email = tk.Entry(fenetre_connexion, width=25)
    champ_email.pack(pady=5)

    tk.Label(fenetre_connexion, text="Mot de passe :", font=("Times New Roman", 12)).pack(pady=5)
    champ_mdp = tk.Entry(fenetre_connexion, show="*", width=25)
    champ_mdp.pack(pady=5)

    btn_connexion = tk.Button(fenetre_connexion, text="Se connecter", command=se_connecter, font=("Times New Roman", 12))
    btn_connexion.pack(pady=10)

    btn_inscription = tk.Button(fenetre_connexion, text="S'inscrire", command=creer_compte, font=("Times New Roman", 12))
    btn_inscription.pack(pady=10)

    btn_modifier_mdp = tk.Button(fenetre_connexion, text="Modifier mot de passe", command=modifier_mdp, font=("Times New Roman", 12))
    btn_modifier_mdp.pack(pady=10)

    fenetre_connexion.mainloop()

connexion_interface()
