<#import "template.ftl" as layout>

<@layout.registrationLayout displayInfo=true displayWide=false>
    <#if section == "header">
        <#include "includes/header.ftl">
    <#elseif section == "form">
        <section class="keur-login__wrapper">
            <div class="keur-login__container">
                <div>
                    <p class="keur-section__eyebrow">${msg('updatePasswordTitle')}</p>
                    <h2 class="keur-section__title">${msg('password')}</h2>
                    <p class="keur-section__description">${msg('updatePasswordMessage','Choisissez un mot de passe solide pour protéger votre compte.')}</p>
                </div>

                <div class="keur-card">
                    <div class="keur-card__header">
                        <h3 class="keur-card__title">${msg('updatePasswordTitle')}</h3>
                        <p class="keur-card__description">${msg('updatePasswordInstruction','Merci d\'actualiser votre mot de passe pour continuer vers Keur Doctor.')}</p>
                    </div>
                    <div class="keur-card__content">
                        <#if message?has_content>
                            <div class="alert ${message.type}">${kcSanitize(message.summary)?no_esc}</div>
                        </#if>
                        <form action="${url.loginAction}" method="post">
                            <div class="keur-field">
                                <label class="keur-label" for="password-new">${msg('passwordNew')}</label>
                                <input id="password-new" class="keur-input" name="password-new" type="password" autocomplete="new-password" autofocus />
                            </div>
                            <div class="keur-field">
                                <label class="keur-label" for="password-confirm">${msg('passwordConfirm')}</label>
                                <input id="password-confirm" class="keur-input" name="password-confirm" type="password" autocomplete="new-password" />
                            </div>
                            <button class="keur-button" type="submit">${msg('doSubmit')}</button>
                        </form>
                    </div>
                </div>
            </div>
        </section>
    <#elseif section == "info">
        <#include "includes/footer.ftl">
    </#if>
</@layout.registrationLayout>
