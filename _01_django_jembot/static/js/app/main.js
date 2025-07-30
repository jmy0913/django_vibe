const sideButtonHandler = () => {
    document.addEventListener('DOMContentLoaded', function () {
        const $buttons = document.querySelectorAll('#news-button, #stock-button');
        const $news_container = document.querySelector('#news-container');
        const $stock_container = document.querySelector('#stock-container');

        const $newsButton = document.querySelector('#news-button');
        if ($newsButton) {
            $newsButton.classList.add('active');
        }

        $buttons.forEach(button => {
                button.addEventListener('click', function () {
                console.log(`${this.textContent} 버튼 클릭`);

                $buttons.forEach(btn => {
                    btn.classList.remove('active');
                });

                this.classList.add('active');
 
                if (this.id === 'news-button') {
                    $news_container.style.display = 'block';
                    $stock_container.style.display = 'none';
                } else if (this.id === 'stock-button') {
                    $stock_container.style.display = 'block';
                    $news_container.style.display = 'none';

                }
                });
        });
    });
  };
  
  sideButtonHandler();
  