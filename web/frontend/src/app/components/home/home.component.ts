import { Component, Inject, OnInit } from '@angular/core';
import { DOCUMENT } from '@angular/common';
import { UserService } from "../../services/user/user.service";
import { Stats } from "../../models/Stats";

@Component({
    selector: 'app-home',
    templateUrl: './home.component.html',
    styleUrls: ['./home.component.scss']
})
export class HomeComponent implements OnInit {
    static INVITE_URL = 'https://discordapp.com/oauth2/authorize?client_id=595363392886145046&scope=bot&permissions=388160'
    REPO_URL          = 'https://www.github.com/hamza1311/BitchBot'
    DBOTS_URL         = 'https://discord.bots.gg/bots/595363392886145046'
    DISCORDAPPS_URL   = 'https://discordapps.dev/en-GB/bots/595363392886145046'
    DBL_URL           = 'https://top.gg/bot/595363392886145046'
    LIST_MY_BOTS_URL  = 'https://listmybots.com/bots/595363392886145046'
    BOTLIST_SPACE_URL = 'https://botlist.space/bot/595363392886145046'
    BOD_URL           = 'https://bots.ondiscord.xyz/bots/595363392886145046'
    INVITE_URL = HomeComponent.INVITE_URL // So it can be used in template

    isIframe = false

    stats: Stats =  {
        uptime: {minutes: 0, seconds: 0, hours: 0, days: 0, human_friendly: '', total_seconds: '0'},
        commands: 0,
        users: 0,
        channels: 0,
        guilds: 0,
    };

    constructor(
        @Inject(DOCUMENT) private document: Document,
        private userService: UserService,
    ) {
        this.isIframe = this.document.location.href.toLowerCase().includes('iframe')
    }

    ngOnInit(): void {
        const targets = document.getElementById('features-grid').querySelectorAll('img');
        const lazyLoad = target => {
            const io = new IntersectionObserver((entries, observer) => {
                console.log(entries)
                entries.forEach(entry => {
                    console.log('😍');

                    if (entry.isIntersecting) {
                        const img = entry.target;
                        const src = img.getAttribute('data-lazy');
                        console.log(src)
                        img.setAttribute('src', src);
                        img.classList.add('fade');

                        observer.disconnect();
                    }
                });
            });

            io.observe(target)
        };
        targets.forEach(lazyLoad);
        this.userService.fetchMyStats().then(resp => {
            this.stats = resp
        })
    }

    setHrefTo(url) {
        this.document.location.href = url
    }
}
