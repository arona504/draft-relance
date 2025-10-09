<header class="kc-header">
    <div class="kc-header__brand">
        <#if properties.kcLogo?has_content>
            <img src="${kcSanitize(properties.kcLogo)}" alt="${msg('loginTitle',realm.displayName)}" class="kc-header__logo"/>
        </#if>
        <div>
            <p class="kc-header__eyebrow">${msg('keur.doctor.tagline','Plateforme multi-tenant de coordination médicale')}</p>
            <h1 class="kc-header__title">${msg('keur.doctor.title','Keur Doctor')}</h1>
        </div>
    </div>
</header>
