<#import "template.ftl" as layout>

<@layout.registrationLayout displayInfo=true displayWide=false>
    <#if section == "header">
        <#include "includes/header.ftl">
    <#elseif section == "form">
        <section class="keur-login__wrapper">
            <div class="keur-login__container">
                <div>
                    <p class="keur-section__eyebrow">${msg("passwordResetTitle")}</p>
                    <h2 class="keur-section__title">${msg("emailForgotTitle")}</h2>
                    <p class="keur-section__description">${msg("emailInstruction","Indiquez votre adresse pour recevoir un lien de réinitialisation.")}</p>
                </div>

                <div class="keur-card">
                    <div class="keur-card__header">
                        <h3 class="keur-card__title">${msg("emailForgotTitle")}</h3>
                        <p class="keur-card__description">${msg("emailInstruction","Nous vous enverrons un e-mail avec les instructions pour réinitialiser votre mot de passe.")}</p>
                    </div>
                    <div class="keur-card__content">
                        <#if message?has_content>
                            <div class="alert ${message.type}">${kcSanitize(message.summary)?no_esc}</div>
                        </#if>

                        <form id="kc-reset-password-form" action="${url.loginAction}" method="post">
                            <div class="keur-field">
                                <label class="keur-label" for="username">${msg("usernameOrEmail")}</label>
                                <input id="username" name="username" class="keur-input" type="text" autofocus value="${(login.username!'')?html}" />
                            </div>
                            <button class="keur-button" type="submit">${msg("doSubmit")}</button>
                        </form>
                        <a class="keur-link" href="${url.loginUrl}">&larr; ${msg("backToLogin")}</a>
                    </div>
                </div>
            </div>
        </section>
    <#elseif section == "info">
        <#include "includes/footer.ftl">
    </#if>
</@layout.registrationLayout>
