<#import "template.ftl" as layout>

<@layout.registrationLayout displayInfo=true displayWide=true>
    <#if section == "header">
        <#include "includes/header.ftl">
    <#elseif section == "form">
        <div class="keur-login">
            <aside class="keur-hero">
                <div class="keur-hero__content">
                    <span class="keur-hero__badge">${msg('keur.doctor.badge','Plateforme sécurisée')}</span>
                    <h2 class="keur-hero__title">${msg('keur.doctor.pitch','Coordonnez vos équipes, optimisez vos agendas, servez vos patients')}</h2>
                    <p class="keur-hero__description">${msg('keur.doctor.subtitle','Unifiez la prise de rendez-vous et la collaboration inter-tenant pour toutes vos structures de soins au Sénégal.')}</p>
                </div>
                <div class="keur-hero__testimonial">
                    <p class="keur-hero__quote">“${msg('keur.doctor.quote','Keur Doctor a fluidifié notre organisation de manière spectaculaire !')}”</p>
                    <p>${msg('keur.doctor.quote.author','Dr. Awa Diallo — Centre Hospitalier Teranga')}</p>
                </div>
            </aside>
            <section class="keur-login__wrapper">
                <div class="keur-login__container">
                    <div>
                        <p class="keur-section__eyebrow">${msg('keur.doctor.secureAccess','Accès sécurisé')}</p>
                        <h2 class="keur-section__title">${msg('loginTitle', realm.displayName)}</h2>
                        <p class="keur-section__description">${msg('keur.doctor.instructions','Connectez-vous avec votre compte Keycloak fourni par votre structure. Les identifiants locaux sont désactivés.')}</p>
                    </div>

                    <div class="keur-card">
                        <div class="keur-card__header">
                            <h3 class="keur-card__title">${msg('keur.doctor.card.title','Se connecter')}</h3>
                            <p class="keur-card__description">${msg('keur.doctor.card.description','Utilisez vos identifiants Keycloak pour accéder à la console Keur Doctor.')}</p>
                        </div>
                        <div class="keur-card__content">
                            <#if message?has_content>
                                <div class="alert ${message.type}">${kcSanitize(message.summary)?no_esc}</div>
                            </#if>

                            <form id="kc-form-login" onsubmit="return true;" action="${url.loginAction}" method="post">
                                <div class="keur-field">
                                    <label class="keur-label" for="username">${msg('usernameOrEmail')}</label>
                                    <input tabindex="1" id="username" class="keur-input" name="username" type="text" autofocus autocomplete="username" value="${(login.username!'')?html}" />
                                </div>
                                <div class="keur-field">
                                    <label class="keur-label" for="password">${msg('password')}</label>
                                    <input tabindex="2" id="password" class="keur-input" name="password" type="password" autocomplete="current-password" />
                                </div>
                                <div class="kc-form-options">
                                    <#if realm.rememberMe>
                                        <label class="remember-me">
                                            <input tabindex="3" id="rememberMe" name="rememberMe" type="checkbox" <#if login.rememberMe?? && login.rememberMe>checked</#if> />
                                            <span>${msg('rememberMe')}</span>
                                        </label>
                                    </#if>
                                    <#if realm.resetPasswordAllowed>
                                        <a class="keur-link" href="${url.loginResetCredentialsUrl}">${msg('forgotPassword')}</a>
                                    </#if>
                                </div>
                                <button tabindex="4" class="keur-button" name="login" type="submit">${msg('doLogIn')}</button>
                            </form>

                            <div class="keur-separator">${msg('keur.doctor.separator','Ou via vos services d\'identité')}</div>
                            <div class="keur-muted-box">${msg('keur.doctor.sso.help','Le bouton ci-dessous vous redirige vers la page de connexion Keycloak de votre structure.')}</div>
                            <#if social.providers??>
                                <div class="social-providers">
                                    <#list social.providers as p>
                                        <a class="keur-button" href="${p.loginUrl}">${p.displayName}</a>
                                    </#list>
                                </div>
                            </#if>
                        </div>
                        <div class="keur-footer">
                            <p>${msg('keur.doctor.footer.terms','En vous connectant, vous acceptez les politiques internes de sécurité et de confidentialité de votre structure.')}</p>
                            <p>${msg('keur.doctor.footer.support','Support : support@keurdoctor.com')}</p>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    <#elseif section == "info">
        <#include "includes/footer.ftl">
    </#if>
</@layout.registrationLayout>
