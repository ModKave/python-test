from modules.fonction import initialiser_fichiers, preparer_rockyou
from graphique import menu_principal

if __name__ == "__main__":
    # Initialisation des fichiers requis
    initialiser_fichiers()
    preparer_rockyou()

    # Lancer le menu principal
    menu_principal()
