<#import "template.ftl" as layout>

<@layout.registrationLayout displayInfo=true displayWide=false>
    <#if section == "header">
        <#include "includes/header.ftl">
    <#elseif section == "form">
        <section class="keur-login__wrapper">
            <div class="keur-login__container">
                <div>
                    <p class="keur-section__eyebrow">${msg('loginOtpOneTime')}</p>
                    <h2 class="keur-section__title">${msg('doLogIn')}</h2>
                    <p class="keur-section__description">${msg('otpInstruction','Entrez le code reçu via votre méthode MFA pour accéder à Keur Doctor.')}</p>
                </div>

                <div class="keur-card">
                    <div class="keur-card__header">
                        <h3 class="keur-card__title">${msg('loginOtpOneTime')}</h3>
                        <p class="keur-card__description">${msg('otpHelpText','Le code expire rapidement, veillez à le saisir sans délai.')}</p>
                    </div>
                    <div class="keur-card__content">
                        <#if message?has_content>
                            <div class="alert ${message.type}">${kcSanitize(message.summary)?no_esc}</div>
                        </#if>

                        <form action="${url.loginAction}" method="post">
                            <div class="keur-field">
                                <label class="keur-label" for="otp">${msg('loginOtpOneTime')}</label>
                                <input id="otp" name="otp" class="keur-input" type="text" autocomplete="one-time-code" autofocus />
                            </div>
                            <button class="keur-button" type="submit">${msg('doLogIn')}</button>
                        </form>
                        <a class="keur-link" href="${url.loginUrl}">&larr; ${msg('backToLogin')}</a>
                    </div>
                </div>
            </div>
        </section>
    <#elseif section == "info">
        <#include "includes/footer.ftl">
    </#if>
</@layout.registrationLayout>
