document.addEventListener('DOMContentLoaded', () => {
    // Button animation for any button with id="animateBtn"
    const btn = document.getElementById('animateBtn');
    if (btn) {
        btn.addEventListener('click', () => {
            btn.style.transform = 'scale(1.1)';
            setTimeout(() => btn.style.transform = 'scale(1)', 200);
        });
    }

    // Background animation with moving lines
    const backgroundDiv = document.getElementById('background');
    if (backgroundDiv) {
        const canvas = document.createElement('canvas');
        backgroundDiv.appendChild(canvas);
        const ctx = canvas.getContext('2d');
        const parentContainer = backgroundDiv.parentElement;
        canvas.width = parentContainer.offsetWidth;
        canvas.height = parentContainer.offsetHeight;
        canvas.style.pointerEvents = 'none';

        const lines = [];
        const numLines = 40;
        const maxDistance = 200;

        class Line {
            constructor() {
                this.x = Math.random() * canvas.width;
                this.y = Math.random() * canvas.height;
                this.angle = Math.random() * Math.PI * 2;
                this.length = Math.random() * 100 + 50;
                this.speed = (Math.random() - 0.5) * 0.03;
                this.velocityX = (Math.random() - 0.5) * 3;
                this.velocityY = (Math.random() - 0.5) * 3;
            }

            draw() {
                ctx.beginPath();
                ctx.moveTo(this.x, this.y);
                const endX = this.x + Math.cos(this.angle) * this.length;
                const endY = this.y + Math.sin(this.angle) * this.length;
                ctx.lineTo(endX, endY);
                ctx.strokeStyle = '#000000';
                ctx.lineWidth = 3;
                ctx.stroke();
                return { endX, endY };
            }

            update() {
                this.angle += this.speed;
                this.x += this.velocityX;
                this.y += this.velocityY;
                if (this.x < 0 || this.x > canvas.width) this.velocityX *= -1;
                if (this.y < 0 || this.y > canvas.height) this.velocityY *= -1;
                return this.draw();
            }
        }

        for (let i = 0; i < numLines; i++) lines.push(new Line());

        function animate() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            const endpoints = [];
            lines.forEach(line => {
                const { endX, endY } = line.update();
                endpoints.push({ x: line.x, y: line.y }, { x: endX, y: endY });
            });

            for (let i = 0; i < endpoints.length; i++) {
                for (let j = i + 1; j < endpoints.length; j++) {
                    const dx = endpoints[i].x - endpoints[j].x;
                    const dy = endpoints[i].y - endpoints[j].y;
                    const distance = Math.sqrt(dx * dx + dy * dy);
                    if (distance < maxDistance) {
                        ctx.beginPath();
                        ctx.moveTo(endpoints[i].x, endpoints[i].y);
                        ctx.lineTo(endpoints[j].x, endpoints[j].y);
                        ctx.strokeStyle = `rgba(0, 0, 0, ${1 - distance / maxDistance})`;
                        ctx.lineWidth = 2;
                        ctx.stroke();
                    }
                }
            }
            requestAnimationFrame(animate);
        }

        animate();
        window.addEventListener('resize', () => {
            canvas.width = parentContainer.offsetWidth;
            canvas.height = parentContainer.offsetHeight;
        });
    }

    // Check URL status for status dots
    const statusDots = document.querySelectorAll('.status-dot');
    statusDots.forEach(dot => {
        const url = dot.getAttribute('data-url');
        if (url) {
            fetch(url, { method: 'HEAD', mode: 'no-cors' })
                .then(() => dot.classList.add('up'))
                .catch(() => dot.classList.add('down'));
        }
    });

    // Add Bookmark popup functionality
    const addBookmarkBtn = document.getElementById('addBookmarkBtn');
    const bookmarkPopup = document.getElementById('bookmarkPopup');
    const closePopup = document.getElementById('closePopup');

    if (addBookmarkBtn && bookmarkPopup && closePopup) {
        bookmarkPopup.style.display = 'none';
        addBookmarkBtn.addEventListener('click', () => {
            console.log('Add Bookmark clicked');
            bookmarkPopup.style.display = 'flex';
        });
        closePopup.addEventListener('click', () => {
            console.log('Close button clicked');
            bookmarkPopup.style.display = 'none';
        });
        bookmarkPopup.addEventListener('click', (e) => {
            if (e.target === bookmarkPopup) {
                console.log('Clicked outside popup');
                bookmarkPopup.style.display = 'none';
            }
        });
    }

    // Client-side validation for image_link fields in forms
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', (e) => {
            const imageLink = form.querySelector('input[name="image_link"]');
            if (imageLink && imageLink.value) {
                const urlPattern = /^(https?:\/\/[^\s/$.?#].[^\s]*)$|^(\/static\/images\/.*)$/;
                if (!urlPattern.test(imageLink.value)) {
                    e.preventDefault();
                    alert('Invalid image URL. Must start with http:// or https://, or be a local path like /static/images/...');
                }
            }
        });
    });
});
