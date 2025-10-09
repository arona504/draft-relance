# Thème Keycloak « keur-login »

Thème personnalisé reproduisant le bloc **Login 02** de shadcn/ui pour l’écran d’authentification Keycloak utilisé par Keur Doctor. Il conserve toutes les fonctionnalités natives (MFA, messages d’erreur, formulaires de réinitialisation, etc.).

## Arborescence

```
themes/keur-login/
├── README.md
└── login/
    ├── theme.properties
    ├── resources
    │   ├── css/login.css
    │   ├── img/keur-logo.svg        # à remplacer par votre logo si besoin
    │   └── fonts/                   # espace réservé si vous ajoutez des polices self-hosted
    └── templates
        ├── includes/header.ftl
        ├── includes/footer.ftl
        ├── login.ftl
        ├── login-reset-password.ftl
        ├── login-update-password.ftl
        └── login-otp.ftl
```

## Installation

1. Copiez le dossier `themes/keur-login` dans l’arborescence `themes/` de votre serveur Keycloak (par exemple, via un volume Docker ou un `docker cp`).
   ```bash
   docker cp themes/keur-login <nom-conteneur-keycloak>:/opt/keycloak/themes/
   ```
2. Redémarrez Keycloak si nécessaire.
3. Dans l’Admin Console Keycloak : **Realm Settings → Themes → Login Theme** puis sélectionnez `keur-login`.
4. Sauvegardez. Le nouvel écran de connexion est immédiatement actif.

## Personnalisation & maintenance

- **Logos / couleurs** : remplacez `login/resources/img/keur-logo.svg` et ajustez les variables CSS définies en début de `login/resources/css/login.css` (`--keur-bg`, `--keur-card`, etc.).
- **Typographie** : la feuille CSS importe la police « Inter ». Ajoutez vos fichiers dans `login/resources/fonts/` et référencez-les dans `login.css` si vous souhaitez une police dédiée.
- **Illustration** : mettez à jour les styles `.keur-hero` dans `login/resources/css/login.css` pour changer le visuel ou la couleur du panneau gauche.
- **Textes** : les traductions utilisent des clés `msg('...')`. Ajoutez-les/dans vos fichiers i18n du parent si vous voulez une traduction spécifique (ex. `messages_fr.properties`). Les chaînes par défaut sont incluses dans les templates (fallback).
- **CSS/Tailwind** : le style est déjà compilé en CSS standard. Pour modifier le design, éditez directement `login.css`. Vous pouvez réutiliser Tailwind/shadcn comme référence visuelle, mais aucune étape de build n’est requise côté Keycloak.

## Fonctionnalités conservées

- Authentification classique (mot de passe) + social providers si configurés
- MFA / OTP (template `login-otp.ftl`)
- Réinitialisation et mise à jour de mot de passe
- Messages d’erreur / d’information Keycloak
- Support multi-langue (français et anglais déclarés dans `theme.properties`)

## Conseils de mise à jour

- Surveillez les changements de version Keycloak : si la structure des formulaires évolue, comparez avec le thème `base` pour appliquer les mêmes variables (`kcSanitize`, identifiants d’inputs...).
- Utilisez un dépôt Git pour suivre les modifications du thème (CSS/FTL). Testez sur un environnement de staging avant déploiement.
- Si vous ajoutez de nouvelles ressources (icônes, images d’aide), placez-les dans `resources/` et mettez à jour les chemins utilisés dans les templates.

Ce thème assure une continuité graphique avec le frontend Next.js reproduisant le bloc « Login 02 » de shadcn/ui, tout en respectant le flux OIDC (redirection vers Keycloak → retour application) sans exposer les tokens côté client.
