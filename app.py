<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Elite Clicker | Telegram Mini App</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --primary-blue: #2A7FFF;
            --dark-blue: #1A5BB2;
            --light-blue: #E6F0FF;
            --white: #FFFFFF;
            --gray: #F5F7FA;
            --dark-gray: #6C7883;
            --shadow: 0 8px 24px rgba(42, 127, 255, 0.2);
            --transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Montserrat', sans-serif;
        }

        body {
            background-image: url('/static/phon.jpg');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            color: #2C3E50;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        .header {
            display: flex;
            justify-content: flex-end;
            padding: 16px;
        }

        .info-btn {
            background-color: var(--primary-blue);
            color: var(--white);
            border: none;
            border-radius: 50px;
            padding: 10px 20px;
            font-weight: 600;
            font-size: 14px;
            cursor: pointer;
            box-shadow: var(--shadow);
            transition: var(--transition);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .info-btn:hover {
            background-color: var(--dark-blue);
            transform: translateY(-2px);
        }

        .info-btn:active {
            transform: translateY(0);
        }

        .sound-control {
            position: fixed;
            top: 80px;
            right: 20px;
            width: 40px;
            height: 40px;
            background-color: var(--primary-blue);
            color: var(--white);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            box-shadow: var(--shadow);
            z-index: 100;
            transition: var(--transition);
        }

        .sound-control:hover {
            background-color: var(--dark-blue);
            transform: scale(1.1);
        }

        .sound-control.muted {
            background-color: var(--dark-gray);
        }

        .sound-control.muted i {
            color: var(--white);
        }

        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 24px;
            text-align: center;
            margin: 20px;
            border-radius: 16px;
        }

        .title {
            color: var(--dark-blue);
            margin-bottom: 8px;
            font-size: 24px;
            font-weight: 700;
        }

        .subtitle {
            color: var(--dark-gray);
            margin-bottom: 24px;
            font-size: 14px;
        }

        .clicker-container {
            position: relative;
            margin: 32px 0;
        }

        .clicker-image {
            width: 240px;
            height: 240px;
            border-radius: 50%;
            object-fit: cover;
            cursor: pointer;
            transition: var(--transition);
            border: 4px solid var(--primary-blue);
            background-color: rgba(42, 127, 255, 0.1);
            box-shadow: 0 0 0 8px rgba(42, 127, 255, 0.2);
        }
        .clicker-image:active {
            transform: scale(0.95);
            background-color: rgba(42, 127, 255, 0.15);
        }

        .click-effect {
            position: absolute;
            width: 60px;
            height: 60px;
            background-color: rgba(255, 255, 255, 0.8);
            border-radius: 50%;
            pointer-events: none;
            animation: clickAnimation 0.6s ease-out;
            transform: translate(-50%, -50%);
            opacity: 0;
        }

        @keyframes clickAnimation {
            0% {
                transform: translate(-50%, -50%) scale(0.2);
                opacity: 1;
            }
            100% {
                transform: translate(-50%, -50%) scale(1.5);
                opacity: 0;
            }
        }

        .stats-container {
            background-color: var(--white);
            border-radius: 16px;
            padding: 20px;
            width: 100%;
            max-width: 320px;
            box-shadow: var(--shadow);
            margin-top: 24px;
        }

        .stat-item {
            display: flex;
            justify-content: space-between;
            margin-bottom: 12px;
        }

        .stat-item:last-child {
            margin-bottom: 0;
        }

        .stat-label {
            color: var(--dark-gray);
            font-weight: 500;
        }

        .stat-value {
            color: var(--dark-blue);
            font-weight: 700;
        }

        .click-counter {
            font-size: 24px;
            font-weight: 700;
            color: var(--primary-blue);
            margin-bottom: 8px;
        }

        .regen-bar {
            height: 8px;
            background-color: var(--light-blue);
            border-radius: 4px;
            margin-top: 12px;
            overflow: hidden;
        }

        .regen-progress {
            height: 100%;
            background-color: var(--primary-blue);
            border-radius: 4px;
            transition: width 0.5s ease;
        }

        .upgrade-btn {
            background-color: var(--primary-blue);
            color: var(--white);
            border: none;
            border-radius: 12px;
            padding: 14px 24px;
            font-weight: 600;
            font-size: 16px;
            cursor: pointer;
            box-shadow: var(--shadow);
            transition: var(--transition);
            margin-top: 24px;
            width: 100%;
            max-width: 320px;
        }

        .upgrade-btn:hover {
            background-color: var(--dark-blue);
            transform: translateY(-2px);
        }

        .upgrade-btn:active {
            transform: translateY(0);
        }

        .notification {
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background-color: var(--primary-blue);
            color: var(--white);
            padding: 12px 24px;
            border-radius: 50px;
            font-weight: 600;
            box-shadow: var(--shadow);
            opacity: 0;
            transition: opacity 0.3s ease;
            z-index: 1000;
            pointer-events: none;
        }

        .notification.show {
            opacity: 1;
        }

        .nav-bar {
            display: flex;
            justify-content: space-around;
            align-items: center;
            background-color: var(--white);
            padding: 10px 0;
            box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
            position: sticky;
            bottom: 0;
            width: 100%;
        }

        .nav-btn {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background: none;
            border: none;
            cursor: pointer;
            padding: 5px 10px;
            border-radius: 10px;
            transition: var(--transition);
        }

        .nav-btn:hover {
            background-color: var(--light-blue);
        }

        .nav-btn img {
            width: 30px;
            height: 30px;
            object-fit: contain;
            margin-bottom: 5px;
        }

        .nav-btn span {
            font-size: 12px;
            color: var(--dark-blue);
            font-weight: 500;
        }

        .active-nav {
            background-color: var(--light-blue);
        }

        .page {
            display: none;
            flex: 1;
            padding: 20px;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
        }

        .page.active {
            display: flex;
        }

        .soon-page {
            font-size: 24px;
            font-weight: 700;
            color: var(--dark-blue);
        }

        /* Обновленные стили для профиля */
        .profile-page {
            width: 100%;
            max-width: 320px;
            background-color: var(--white);
            padding: 20px;
            border-radius: 16px;
            box-shadow: var(--shadow);
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .profile-username {
            font-size: 18px;
            font-weight: 700;
            color: var(--dark-blue);
            text-align: center;
            margin-bottom: 10px;
        }

        .profile-icons-container {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
        }

        .profile-icon {
            background-color: rgba(42, 127, 255, 0.1);
            border: 1px solid var(--primary-blue);
            border-radius: 12px;
            padding: 15px;
            width: 48%;
            min-height: 80px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            transition: var(--transition);
        }

        .profile-icon:hover {
            background-color: rgba(42, 127, 255, 0.2);
        }

        .profile-icon-large {
            width: 100%;
            min-height: 100px;
            background-color: rgba(42, 127, 255, 0.15);
        }

        .profile-icon-title {
            font-size: 14px;
            color: var(--dark-gray);
            margin-bottom: 5px;
        }

        .profile-icon-value {
            font-size: 18px;
            font-weight: 700;
            color: var(--primary-blue);
        }

        .profile-exchange-btn {
            background-color: var(--primary-blue);
            color: var(--white);
            border: none;
            border-radius: 12px;
            padding: 16px;
            font-weight: 600;
            font-size: 16px;
            cursor: pointer;
            box-shadow: var(--shadow);
            transition: var(--transition);
            width: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
        }

        .profile-exchange-btn:hover {
            background-color: var(--dark-blue);
            transform: translateY(-2px);
        }

        .profile-exchange-btn:active {
            transform: translateY(0);
        }

        .profile-exchange-icon {
            font-size: 24px;
        }

        .profile-rank-info {
            display: flex;
            justify-content: space-between;
            width: 100%;
            margin-top: 10px;
        }

        .profile-rank-item {
            text-align: center;
            cursor: pointer;
        }

        .profile-rank-label {
            font-size: 12px;
            color: var(--dark-gray);
        }

        .profile-rank-value {
            font-size: 14px;
            font-weight: 600;
            color: var(--primary-blue);
        }

        /* Стили для страницы заданий */
        .tasks-container {
            width: 100%;
            max-width: 320px;
            background-color: var(--white);
            padding: 24px;
            border-radius: 16px;
            box-shadow: var(--shadow);
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        
        .tasks-title {
            color: var(--dark-blue);
            margin-bottom: 4px;
            font-size: 22px;
            font-weight: 700;
            text-align: center;
        }
        
        .tasks-description {
            color: var(--dark-gray);
            font-size: 14px;
            text-align: center;
            margin-bottom: 12px;
        }
        
        /* Новые стили для кнопок заданий */
        .task-button-container {
            display: flex;
            width: 100%;
            margin-bottom: 12px;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        .task-channel-btn {
            flex-grow: 1;
            background: white;
            color: black;
            border: none;
            padding: 12px 16px;
            text-align: left;
            font-weight: 500;
            text-decoration: none;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .task-channel-name {
            flex-grow: 1;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .task-reward {
            color: var(--primary-blue);
            font-weight: 600;
            margin-left: 8px;
            white-space: nowrap;
        }
        
        .task-check-btn {
            background: var(--primary-blue);
            color: white;
            border: none;
            padding: 12px 16px;
            font-weight: 500;
            cursor: pointer;
            white-space: nowrap;
            transition: var(--transition);
        }
        
        .task-check-btn:hover {
            background: var(--dark-blue);
        }

        /* Остальные стили остаются без изменений */
    </style>
</head>
<body>
    <div class="header">
        <button class="info-btn" id="infoBtn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M12 16V12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M12 8H12.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            Info
        </button>
    </div>
    
    <div class="sound-control muted" id="soundControl">
        <i class="fas fa-volume-mute"></i>
    </div>
    
    <audio id="backgroundMusic" loop preload="auto">
        <source src="/static/Waterflame_FieldofMemories.mp3" type="audio/mpeg">
    </audio>
    
    <div id="mainPage" class="page active">
        <div class="main-content">
            <h1 class="title">Elite Clicker</h1>
            <p class="subtitle">Нажимайте на изображение для получения $DGR</p>
            
            <div class="clicker-container" id="clickerContainer">
                <img src="/static/IMG_8264.PNG" alt="Click me" class="clicker-image" id="clickerImage">
            </div>
            
            <div class="stats-container">
                <div class="click-counter">Баланс: <span id="totalClicks">0</span> $DGR</div>
                <div class="stat-item">
                    <span class="stat-label">Доступно кликов:</span>
                    <span class="stat-value" id="availableClicks">100</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Сила клика:</span>
                    <span class="stat-value" id="clickPower">1</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Восстановление:</span>
                    <span class="stat-value" id="regenRate">1 клик/сек</span>
                </div>
                <div class="regen-bar">
                    <div class="regen-progress" id="regenProgress" style="width: 100%"></div>
                </div>
            </div>
            
            <button class="upgrade-btn" id="upgradeBtn">Улучшения</button>
            
            <button class="upgrade-btn ranking-btn" id="rankingBtn" style="margin-top: 12px;">Рейтинг игроков</button>
        </div>
    </div>

    <div id="upgradesPage" class="page">
        <div class="page-content">
            <h2 class="title">Улучшения</h2>
            <p class="subtitle">Улучшайте параметры для увеличения эффективности</p>
            
            <div class="upgrades-container">
                <div class="upgrade-card" id="clickUpgrade">
                    <div class="upgrade-icon">
                        <i class="fas fa-hand-pointer"></i>
                    </div>
                    <div class="upgrade-info">
                        <h3>Мощность клика</h3>
                        <p class="upgrade-description">Увеличивает количество $DGR за один клик</p>
                        <div class="upgrade-level">
                            <span class="level-label">Уровень:</span>
                            <span class="level-value" id="clickUpgradeLevel">0</span>
                            <span class="level-max">/12</span>
                        </div>
                        <div class="upgrade-bonus" id="clickUpgradeBonus">+2 $DGR за клик</div>
                    </div>
                    <button class="upgrade-purchase-btn" id="clickUpgradeBtn">
                        <span class="upgrade-cost" id="clickUpgradeCost">200 $DGR</span>
                    </button>
                </div>
                
                <div class="upgrade-card" id="storageUpgrade">
                    <div class="upgrade-icon">
                        <i class="fas fa-database"></i>
                    </div>
                    <div class="upgrade-info">
                        <h3>Объем хранилища</h3>
                        <p class="upgrade-description">Увеличивает максимальное количество доступных тапов</p>
                        <div class="upgrade-level">
                            <span class="level-label">Уровень:</span>
                            <span class="level-value" id="storageUpgradeLevel">0</span>
                            <span class="level-max">/12</span>
                        </div>
                        <div class="upgrade-bonus" id="storageUpgradeBonus">+20 тапов</div>
                    </div>
                    <button class="upgrade-purchase-btn" id="storageUpgradeBtn">
                        <span class="upgrade-cost" id="storageUpgradeCost">200 $DGR</span>
                    </button>
                </div>
                
                <div class="upgrade-card" id="speedUpgrade">
                    <div class="upgrade-icon">
                        <i class="fas fa-clock"></i>
                    </div>
                    <div class="upgrade-info">
                        <h3>Скорость восстановления</h3>
                        <p class="upgrade-description">Уменьшает время восстановления тапов</p>
                        <div class="upgrade-level">
                            <span class="level-label">Уровень:</span>
                            <span class="level-value" id="speedUpgradeLevel">0</span>
                            <span class="level-max">/12</span>
                        </div>
                        <div class="upgrade-bonus" id="speedUpgradeBonus">-0.05 сек на тап</div>
                    </div>
                    <button class="upgrade-purchase-btn" id="speedUpgradeBtn">
                        <span class="upgrade-cost" id="speedUpgradeCost">2000 $DGR</span>
                    </button>
                </div>
            </div>
            
            <button class="back-button" id="upgradesBackBtn">
                <i class="fas fa-arrow-left"></i> Назад
            </button>
        </div>
    </div>
    
    <div class="page" id="rankingPage">
        <div class="ranking-container">
            <h2 class="ranking-title">Рейтинг игроков</h2>
            <p class="ranking-description">Список игроков с наивысшим балансом $DGR</p>
            
            <div class="ranking-list-container">
                <div class="ranking-header">
                    <div class="rank-column">Место</div>
                    <div class="user-column">Игрок</div>
                    <div class="balance-column">Баланс</div>
                </div>
                
                <div class="ranking-list" id="rankingList">
                    <!-- Будет заполнено динамически -->
                    <div class="ranking-list-loading">
                        <i class="fas fa-spinner fa-spin"></i> Загрузка рейтинга...
                    </div>
                </div>
            </div>
            
            <div class="your-rank">
                <span class="your-rank-label">Ваше место:</span>
                <span class="your-rank-value" id="yourRank">--</span>
            </div>
        </div>
    </div>
    
    <div class="page" id="referralRankingPage">
        <div class="referral-ranking-container">
            <h2 class="referral-ranking-title">Топ по рефералам</h2>
            <p class="referral-ranking-description">Список игроков с наибольшим количеством приглашенных друзей</p>
            
            <div class="referral-ranking-list-container">
                <div class="referral-ranking-header">
                    <div class="referral-rank-column">Место</div>
                    <div class="referral-user-column">Игрок</div>
                    <div class="referral-count-column">Рефералы</div>
                </div>
                
                <div class="referral-ranking-list" id="referralRankingList">
                    <!-- Будет заполнено динамически -->
                    <div class="referral-ranking-list-loading">
                        <i class="fas fa-spinner fa-spin"></i> Загрузка рейтинга...
                    </div>
                </div>
            </div>
            
            <div class="your-referral-rank">
                <span class="your-referral-rank-label">Ваше место:</span>
                <span class="your-referral-rank-value" id="yourReferralRank">--</span>
            </div>
        </div>
    </div>
    
    <div class="page" id="tasksPage">
        <div class="tasks-container">
            <h2 class="tasks-title">Задания</h2>
            <p class="tasks-description">Выполняйте задания и получайте награды в $DGR</p>
            
            <div id="tasksList">
                <!-- Tasks will be loaded here dynamically -->
            </div>
        </div>
    </div>
    
    <div class="page" id="profilePage">
        <div class="profile-page">
            <div class="profile-username" id="profileUsername">Пользователь</div>
            
            <div class="profile-icons-container">
                <div class="profile-icon">
                    <div class="profile-icon-title">Баланс</div>
                    <div class="profile-icon-value" id="profileBalanceValue">0 $DGR</div>
                </div>
                
                <div class="profile-icon">
                    <div class="profile-icon-title">Друзья</div>
                    <div class="profile-icon-value" id="profileFriendsValue">0</div>
                </div>
                
                <button class="profile-icon profile-icon-large profile-exchange-btn" id="exchangeBtn">
                    <i class="fas fa-exchange-alt profile-exchange-icon"></i>
                    <span>Обмен</span>
                </button>
                
                <div class="profile-rank-info">
                    <div class="profile-rank-item" id="balanceRankItem">
                        <div class="profile-rank-label">Топ по балансу</div>
                        <div class="profile-rank-value" id="balanceRankValue">--</div>
                    </div>
                    
                    <div class="profile-rank-item" id="referralsRankItem">
                        <div class="profile-rank-label">Топ по друзьям</div>
                        <div class="profile-rank-value" id="referralsRankValue">--</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="page" id="friendsPage">
        <div class="referral-container">
            <h2 class="referral-title">Пригласите друзей</h2>
            <p class="referral-description">Делитесь ссылкой с друзьями и получайте бонусы за каждого приглашенного пользователя!</p>
            
            <div class="referral-link-container">
                <input type="text" readonly id="referralLink" class="referral-link" value="">
                <button id="copyLinkBtn" class="copy-btn">
                    <i class="fas fa-copy"></i>
                </button>
            </div>
            
            <div class="referral-stats">
                <div class="referral-stat-icon">
                    <i class="fas fa-user-plus"></i>
                </div>
                <div class="referral-stat-info">
                    <span class="referral-stat-label">Вы пригласили:</span>
                    <span class="referral-stat-value" id="referralCount">0</span>
                </div>
            </div>
            
            <div class="referral-earnings">
                <div class="earnings-header">
                    <h3 class="earnings-title">Доход от рефералов</h3>
                    <div class="claim-container">
                        <span class="claim-amount" id="claimableAmount">0 $DGR</span>
                        <button class="claim-btn" id="claimBtn">
                            <i class="fas fa-hand-holding-usd"></i> Claim
                        </button>
                    </div>
                </div>
                <div class="claim-timer" id="claimTimer">Доступно через: <span id="nextClaimTime">00:00:00</span></div>
                
                <ul class="referrals-list" id="referralsList">
                    <!-- Список будет заполнен динамически -->
                    <li class="referral-list-placeholder">У вас пока нет рефералов</li>
                </ul>
                
                <div class="more-referrals" id="moreReferrals">
                    <span>И еще <span id="hiddenReferralsCount">0</span> рефералов</span>
                </div>
            </div>
            
            <div class="referral-benefits">
                <h3 class="benefits-title">Преимущества приглашения:</h3>
                <ul class="benefits-list">
                    <li><i class="fas fa-check"></i> +10,000 $DGR за каждого приглашенного друга</li>
                    <li><i class="fas fa-check"></i> 10% от заработка ваших рефералов</li>
                    <li><i class="fas fa-check"></i> Возможность собирать доход каждые 8 часов</li>
                </ul>
            </div>
        </div>
    </div>
    
    <div class="nav-bar">
        <button class="nav-btn" id="tasksBtn">
            <img src="/static/task.jpg" alt="Задания">
            <span>Задания</span>
        </button>
        <button class="nav-btn" id="friendsBtn">
            <img src="/static/freands.jpg" alt="Друзья">
            <span>Друзья</span>
        </button>
        <button class="nav-btn active-nav" id="mainBtn">
            <img src="/static/Menu.jpg" alt="Меню">
            <span>Главная</span>
        </button>
        <button class="nav-btn" id="profileBtn">
            <img src="/static/balance.jpg" alt="Профиль">
            <span>Профиль</span>
        </button>
    </div>
    
    <div class="notification" id="notification"></div>
    
    <script>
        // Инициализация Telegram WebApp
        const tg = window.Telegram.WebApp;
        tg.expand();
        
        // Получаем данные пользователя из Telegram
        const userId = tg.initDataUnsafe.user?.id;
        const username = tg.initDataUnsafe.user?.username || 'Пользователь';
        
        if (!userId) {
            console.error("User ID not found in Telegram WebApp init data");
        }
        
        // Установка имени пользователя в профиле
        document.getElementById('profileUsername').textContent = '@' + username;
        
        // Элементы DOM
        const elements = {
            clickerImage: document.getElementById('clickerImage'),
            clickerContainer: document.getElementById('clickerContainer'),
            totalClicks: document.getElementById('totalClicks'),
            availableClicks: document.getElementById('availableClicks'),
            clickPower: document.getElementById('clickPower'),
            regenRate: document.getElementById('regenRate'),
            regenProgress: document.getElementById('regenProgress'),
            upgradeBtn: document.getElementById('upgradeBtn'),
            rankingBtn: document.getElementById('rankingBtn'),
            infoBtn: document.getElementById('infoBtn'),
            notification: document.getElementById('notification'),
            profileBalanceValue: document.getElementById('profileBalanceValue'),
            profileFriendsValue: document.getElementById('profileFriendsValue'),
            exchangeBtn: document.getElementById('exchangeBtn'),
            balanceRankItem: document.getElementById('balanceRankItem'),
            balanceRankValue: document.getElementById('balanceRankValue'),
            referralsRankItem: document.getElementById('referralsRankItem'),
            referralsRankValue: document.getElementById('referralsRankValue'),
            // Навигационные кнопки
            mainBtn: document.getElementById('mainBtn'),
            tasksBtn: document.getElementById('tasksBtn'),
            profileBtn: document.getElementById('profileBtn'),
            friendsBtn: document.getElementById('friendsBtn'),
            // Страницы
            mainPage: document.getElementById('mainPage'),
            tasksPage: document.getElementById('tasksPage'),
            profilePage: document.getElementById('profilePage'),
            friendsPage: document.getElementById('friendsPage'),
            rankingPage: document.getElementById('rankingPage'),
            referralRankingPage: document.getElementById('referralRankingPage'),
            // Элементы звука
            soundControl: document.getElementById('soundControl'),
            backgroundMusic: document.getElementById('backgroundMusic'),
            // Upgrade page elements
            upgradesPage: document.getElementById('upgradesPage'),
            upgradesBackBtn: document.getElementById('upgradesBackBtn'),
            clickUpgradeBtn: document.getElementById('clickUpgradeBtn'),
            storageUpgradeBtn: document.getElementById('storageUpgradeBtn'),
            speedUpgradeBtn: document.getElementById('speedUpgradeBtn'),
            clickUpgradeLevel: document.getElementById('clickUpgradeLevel'),
            storageUpgradeLevel: document.getElementById('storageUpgradeLevel'),
            speedUpgradeLevel: document.getElementById('speedUpgradeLevel'),
            clickUpgradeCost: document.getElementById('clickUpgradeCost'),
            storageUpgradeCost: document.getElementById('storageUpgradeCost'),
            speedUpgradeCost: document.getElementById('speedUpgradeCost'),
            clickUpgradeBonus: document.getElementById('clickUpgradeBonus'),
            storageUpgradeBonus: document.getElementById('storageUpgradeBonus'),
            speedUpgradeBonus: document.getElementById('speedUpgradeBonus')
        };
        
        // Состояние приложения
        let appState = {
            totalClicks: 0,
            availableClicks: 100,
            clickPower: 1,
            maxClicks: 100,
            regenRate: 1,
            lastUpdate: Date.now(),
            isMuted: true, // По умолчанию звук выключен
            wasInteraction: false,
            referralCount: 0, // Счетчик рефералов
            referrals: [], // Массив с данными о рефералах
            claimableAmount: 0, // Сумма доступная для сбора
            lastClaimTime: null, // Время последнего сбора
            claimCooldown: 8 * 60 * 60 * 1000, // 8 часов в миллисекундах
            balanceRank: '--', // Ранг по балансу
            referralsRank: '--', // Ранг по количеству рефералов
            upgradeLevels: {
                click: { level: 0, cost: 200, maxLevel: 12 },
                storage: { level: 0, cost: 200, maxLevel: 12 },
                speed: { level: 0, cost: 2000, maxLevel: 12 }
            }
        };
        
        // Инициализация музыки
        function initMusic() {
            // Устанавливаем начальную громкость
            elements.backgroundMusic.volume = 0.5;
            
            // Загружаем состояние звука из localStorage
            const savedMuteState = localStorage.getItem('isMuted');
            if (savedMuteState !== null) {
                appState.isMuted = savedMuteState === 'true';
            }
            
            // Обновляем UI звука
            updateSoundUI();
            
            // Обработчик ошибок воспроизведения
            elements.backgroundMusic.addEventListener('error', () => {
                console.error('Audio playback error');
                appState.isMuted = true;
                localStorage.setItem('isMuted', 'true');
                updateSoundUI();
                showNotification('Ошибка воспроизведения звука');
            });
            
            // Обработчик изменения громкости
            elements.backgroundMusic.addEventListener('volumechange', () => {
                if (elements.backgroundMusic.volume === 0) {
                    appState.isMuted = true;
                }
                updateSoundUI();
            });
        }
        
        // Обновление UI звука
        function updateSoundUI() {
            if (appState.isMuted) {
                elements.soundControl.classList.add('muted');
                elements.soundControl.innerHTML = '<i class="fas fa-volume-mute"></i>';
            } else {
                elements.soundControl.classList.remove('muted');
                elements.soundControl.innerHTML = '<i class="fas fa-volume-up"></i>';
            }
        }
        
        // Переключение звука
        function toggleSound() {
            appState.isMuted = !appState.isMuted;
            localStorage.setItem('isMuted', appState.isMuted.toString());
            
            if (appState.isMuted) {
                elements.backgroundMusic.pause();
            } else {
                // Пытаемся воспроизвести только после взаимодействия пользователя
                if (appState.wasInteraction) {
                    elements.backgroundMusic.play()
                        .then(() => {
                            updateSoundUI();
                        })
                        .catch(error => {
                            console.error('Audio playback failed:', error);
                            appState.isMuted = true;
                            localStorage.setItem('isMuted', 'true');
                            updateSoundUI();
                            showNotification('Не удалось включить звук');
                        });
                }
            }
            updateSoundUI();
        }
        
        // Обработчик первого взаимодействия
        function handleFirstInteraction() {
            if (!appState.wasInteraction) {
                appState.wasInteraction = true;
                // Если звук не отключен, пытаемся воспроизвести
                if (!appState.isMuted) {
                    elements.backgroundMusic.play()
                        .then(() => {
                            console.log('Audio started after user interaction');
                        })
                        .catch(error => {
                            console.error('Audio playback after interaction failed:', error);
                        });
                }
            }
        }
        
        // Загрузка данных пользователя
        async function loadUserData() {
            try {
                tg.MainButton.showProgress();
                
                const response = await fetch('/api/user', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Telegram-Init-Data': tg.initData || ''
                    },
                    body: JSON.stringify({ 
                        userId,
                        username: username
                    })
                });
        
                if (!response.ok) {
                    throw new Error('Failed to load user data');
                }
        
                const data = await response.json();
        
                appState = {
                    ...appState,
                    totalClicks: parseInt(data.totalClicks) || 0,
                    availableClicks: parseFloat(data.availableClicks) || 100,
                    clickPower: parseInt(data.clickPower) || 1,
                    maxClicks: parseInt(data.maxClicks) || 100,
                    regenRate: parseFloat(data.regenRate) || 1,
                    lastUpdate: Date.now()
                };
        
                if (data.upgradeLevels) {
                    appState.upgradeLevels = data.upgradeLevels;
                }
        
                updateUI();
                
            } catch (error) {
                console.error('Error loading user data:', error);
                showNotification('Ошибка загрузки данных');
                setTimeout(loadUserData, 5000);
                
            } finally {
                tg.MainButton.hideProgress();
            }
        }
        
        // Обновление UI
        function updateUI() {
            elements.totalClicks.textContent = formatNumber(appState.totalClicks);
            elements.availableClicks.textContent = Math.floor(appState.availableClicks);
            elements.clickPower.textContent = appState.clickPower;
            elements.regenRate.textContent = `${appState.regenRate.toFixed(1)} клик/сек`;
            elements.profileBalanceValue.textContent = `${formatNumber(appState.totalClicks)} $DGR`;
            elements.profileFriendsValue.textContent = appState.referralCount;
    
            const progressPercent = Math.min(100, (appState.availableClicks / appState.maxClicks) * 100);
            elements.regenProgress.style.width = `${progressPercent}%`;
    
            elements.upgradeBtn.disabled = appState.totalClicks < 10;
            
            updateUpgradeButtons();
        }
        
        // Форматирование чисел
        function formatNumber(num) {
            return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
        }
        
        // Обновление кликов
        function updateClicks() {
            const now = Date.now();
            const deltaTime = (now - appState.lastUpdate) / 1000;
            
            if (appState.availableClicks < appState.maxClicks) {
                appState.availableClicks = Math.min(
                    appState.maxClicks,
                    appState.availableClicks + (deltaTime * appState.regenRate)
                );
                appState.lastUpdate = now;
                updateUI();
            }
        }
        
        // Показать уведомление
        function showNotification(message) {
            elements.notification.textContent = message;
            elements.notification.classList.add('show');
            
            setTimeout(() => {
                elements.notification.classList.remove('show');
            }, 3000);
        }
        
        // Обработчик клика
        elements.clickerImage.addEventListener('click', async (e) => {
            handleFirstInteraction();
            
            try {
                const clickEffect = document.createElement('div');
                clickEffect.className = 'click-effect';
                clickEffect.style.left = `${e.offsetX}px`;
                clickEffect.style.top = `${e.offsetY}px`;
                elements.clickerContainer.appendChild(clickEffect);
                
                setTimeout(() => {
                    elements.clickerContainer.removeChild(clickEffect);
                }, 600);
                
                const response = await fetch('/api/user/click', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Telegram-Init-Data': tg.initData || ''
                    },
                    body: JSON.stringify({ userId })
                });
                
                if (!response.ok) {
                    throw new Error('Click failed');
                }
                
                const data = await response.json();
                
                appState.totalClicks = data.totalClicks;
                appState.availableClicks = data.availableClicks;
                updateUI();
                
            } catch (error) {
                console.error('Click error:', error);
                showNotification('Ошибка при клике');
            }
        });
        
        // Обработчики кнопок
        elements.upgradeBtn.addEventListener('click', () => {
            handleFirstInteraction();
            switchPage('upgradesPage');
        });
        
        elements.rankingBtn.addEventListener('click', () => {
            switchPage('rankingPage');
            loadRanking();
        });
        
        elements.infoBtn.addEventListener('click', () => {
            handleFirstInteraction();
            showNotification('Elite Clicker - зарабатывайте $DGR кликами!');
        });
        
        elements.soundControl.addEventListener('click', () => {
            handleFirstInteraction();
            toggleSound();
        });
        
        // Обработчик кнопки обмена
        elements.exchangeBtn.addEventListener('click', () => {
            handleFirstInteraction();
            showNotification('Обмен будет доступен в ближайшее время! 💰');
        });
        
        // Обработчики рейтингов в профиле
        elements.balanceRankItem.addEventListener('click', () => {
            switchPage('rankingPage');
            loadRanking();
        });
        
        elements.referralsRankItem.addEventListener('click', () => {
            switchPage('referralRankingPage');
            loadReferralRanking();
        });
        
        // Переключение страниц
        function switchPage(pageId) {
            document.querySelectorAll('.page').forEach(page => {
                page.classList.remove('active');
            });
            
            document.getElementById(pageId).classList.add('active');
            
            document.querySelectorAll('.nav-btn').forEach(btn => {
                btn.classList.remove('active-nav');
            });
            
            if (pageId === 'mainPage') {
                elements.mainBtn.classList.add('active-nav');
            } else if (pageId === 'tasksPage') {
                elements.tasksBtn.classList.add('active-nav');
                loadTasks(); // Загружаем задания при переходе на страницу
            } else if (pageId === 'profilePage') {
                elements.profileBtn.classList.add('active-nav');
            } else if (pageId === 'friendsPage') {
                elements.friendsBtn.classList.add('active-nav');
                updateReferralUI(); // Обновляем реферальный UI при переключении на страницу
            } else if (pageId === 'rankingPage') {
                elements.rankingBtn.classList.add('active-nav');
                loadRanking();
            }
            
            handleFirstInteraction();
        }
        
        // Генерация реферальной ссылки
        function generateReferralLink() {
            if (!userId) {
                console.error('User ID not available for generating referral link');
                return '';
            }
            
            const baseUrl = 'https://t.me/edfasdasdasbot/Zakazapp';
            const referralParam = `ref=${userId}`;
            
            // Формируем ссылку
            // Telegram Mini App links can use startapp parameter for initial data
            return `${baseUrl}?startapp=${referralParam}`;
        }
        
        // Обработчик копирования реферальной ссылки
        function copyReferralLink() {
            const linkInput = document.getElementById('referralLink');
            linkInput.select();
            linkInput.setSelectionRange(0, 99999); // Для мобильных устройств
            
            navigator.clipboard.writeText(linkInput.value)
                .then(() => {
                    showNotification('Ссылка скопирована!');
                })
                .catch(err => {
                    console.error('Ошибка при копировании: ', err);
                    
                    // Запасной вариант для старых браузеров
                    try {
                        document.execCommand('copy');
                        showNotification('Ссылка скопирована!');
                    } catch (e) {
                        console.error('Ошибка при копировании (запасной вариант): ', e);
                        showNotification('Не удалось скопировать ссылку');
                    }
                });
        }
        
        // Загрузка реферальной статистики
        async function loadReferralStats() {
            if (!userId) {
                console.error('User ID not available for loading referral stats');
                return;
            }
            
            try {
                const response = await fetch('/api/user/referrals', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Telegram-Init-Data': tg.initData || ''
                    },
                    body: JSON.stringify({ userId })
                });
                
                if (!response.ok) {
                    throw new Error('Failed to load referral stats');
                }
                
                const data = await response.json();
                appState.referralCount = data.referralCount || 0;
                appState.referrals = data.referrals || [];
                appState.claimableAmount = data.claimableAmount || 0;
                appState.lastClaimTime = data.lastClaimTime ? new Date(data.lastClaimTime) : null;
                
                // Обновляем UI с реферальной статистикой
                updateReferralUI();
                
            } catch (error) {
                console.error('Error loading referral stats:', error);
                // Если ошибка - устанавливаем дефолтные значения, чтобы UI не сломался
                appState.referralCount = 0;
                appState.referrals = [];
                appState.claimableAmount = 0;
                appState.lastClaimTime = null;
                updateReferralUI();
            }
        }
        
        // Обновление UI реферальной системы
        function updateReferralUI() {
            try {
                // Устанавливаем реферальную ссылку
                const referralLink = generateReferralLink();
                document.getElementById('referralLink').value = referralLink;
                
                // Обновляем счетчик рефералов
                document.getElementById('referralCount').textContent = appState.referralCount;
                elements.profileFriendsValue.textContent = appState.referralCount;
                
                // Обновляем сумму для сбора
                document.getElementById('claimableAmount').textContent = `${formatNumber(appState.claimableAmount)} $DGR`;
                
                // Обновляем статус кнопки Claim
                const claimBtn = document.getElementById('claimBtn');
                let nextClaimTime = '';
                let canClaim = false;
                
                if (appState.lastClaimTime) {
                    const now = new Date();
                    const nextClaimDate = new Date(appState.lastClaimTime.getTime() + appState.claimCooldown);
                    
                    if (now < nextClaimDate) {
                        // Еще не прошло 8 часов
                        const timeLeft = nextClaimDate - now;
                        const hours = Math.floor(timeLeft / (60 * 60 * 1000));
                        const minutes = Math.floor((timeLeft % (60 * 60 * 1000)) / (60 * 1000));
                        const seconds = Math.floor((timeLeft % (60 * 1000)) / 1000);
                        
                        nextClaimTime = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                        canClaim = false;
                    } else {
                        // Прошло более 8 часов
                        nextClaimTime = 'Доступно сейчас';
                        canClaim = (appState.claimableAmount > 0);
                    }
                } else {
                    // Еще ни разу не собирали
                    nextClaimTime = 'Доступно сейчас';
                    canClaim = (appState.claimableAmount > 0);
                }
                
                document.getElementById('nextClaimTime').textContent = nextClaimTime;
                claimBtn.disabled = !canClaim;
                
                // Обновляем список рефералов
                const referralsList = document.getElementById('referralsList');
                referralsList.innerHTML = '';
                
                if (!appState.referrals || appState.referrals.length === 0) {
                    // Нет рефералов
                    const placeholder = document.createElement('li');
                    placeholder.className = 'referral-list-placeholder';
                    placeholder.textContent = 'У вас пока нет рефералов';
                    referralsList.appendChild(placeholder);
                    
                    // Скрываем блок "И еще N рефералов"
                    document.getElementById('moreReferrals').style.display = 'none';
                } else {
                    // Есть рефералы - показываем первые 10
                    const displayCount = Math.min(appState.referrals.length, 10);
                    
                    for (let i = 0; i < displayCount; i++) {
                        const referral = appState.referrals[i];
                        const listItem = document.createElement('li');
                        
                        // Проверяем, есть ли нормальное имя пользователя
                        const displayUsername = referral.username && referral.username !== 'user' ? 
                            referral.username : `User${referral.id % 1000}`;
                        
                        listItem.innerHTML = `
                            <div class="referral-user">
                                <div class="referral-avatar">
                                    ${displayUsername.charAt(0).toUpperCase()}
                                </div>
                                <span class="referral-username">@${displayUsername}</span>
                            </div>
                            <div class="referral-earnings">
                                ${formatNumber(referral.earnings || 0)} $DGR
                            </div>
                        `;
                        
                        referralsList.appendChild(listItem);
                    }
                    
                    // Обновляем блок "И еще N рефералов"
                    const hiddenCount = appState.referralCount - displayCount;
                    if (hiddenCount > 0) {
                        document.getElementById('hiddenReferralsCount').textContent = hiddenCount;
                        document.getElementById('moreReferrals').style.display = 'block';
                    } else {
                        document.getElementById('moreReferrals').style.display = 'none';
                    }
                }
            } catch (error) {
                console.error('Error updating referral UI:', error);
            }
        }
        
        // Функция для сбора дохода от рефералов
        async function claimReferralEarnings() {
            if (!userId) {
                console.error('User ID not available for claiming referral earnings');
                return;
            }
            
            try {
                // Показываем индикатор загрузки 
                const claimBtn = document.getElementById('claimBtn');
                const originalText = claimBtn.innerHTML;
                claimBtn.disabled = true;
                claimBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Загрузка...';
                
                const response = await fetch('/api/user/claim-referrals', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Telegram-Init-Data': tg.initData || ''
                    },
                    body: JSON.stringify({ userId })
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    claimBtn.innerHTML = originalText;
                    claimBtn.disabled = false;
                    throw new Error(errorData.error || 'Failed to claim referral earnings');
                }
                
                const data = await response.json();
                
                // Обновляем данные
                appState.totalClicks += data.claimedAmount;
                appState.claimableAmount = 0;
                appState.lastClaimTime = new Date();
                
                // Обновляем UI
                updateUI();
                updateReferralUI();
                
                // Показываем уведомление
                showNotification(`Получено ${formatNumber(data.claimedAmount)} $DGR от рефералов!`);
                
                // Восстанавливаем кнопку
                claimBtn.innerHTML = originalText;
                claimBtn.disabled = false;
                
            } catch (error) {
                console.error('Error claiming referral earnings:', error);
                showNotification(error.message || 'Ошибка при получении дохода');
            }
        }
        
        // Обновляет таймер для следующего claim каждую секунду
        function startClaimTimer() {
            setInterval(() => {
                if (appState.lastClaimTime) {
                    const now = new Date();
                    const nextClaimDate = new Date(appState.lastClaimTime.getTime() + appState.claimCooldown);
                    
                    if (now < nextClaimDate) {
                        // Еще не прошло 8 часов
                        const timeLeft = nextClaimDate - now;
                        const hours = Math.floor(timeLeft / (60 * 60 * 1000));
                        const minutes = Math.floor((timeLeft % (60 * 60 * 1000)) / (60 * 1000));
                        const seconds = Math.floor((timeLeft % (60 * 1000)) / 1000);
                        
                        const nextClaimTime = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                        document.getElementById('nextClaimTime').textContent = nextClaimTime;
                        document.getElementById('claimBtn').disabled = true;
                    } else {
                        // Прошло более 8 часов
                        document.getElementById('nextClaimTime').textContent = 'Доступно сейчас';
                        document.getElementById('claimBtn').disabled = (appState.claimableAmount <= 0);
                    }
                }
            }, 1000);
        }
        
        // Проверка и обработка реферального параметра
        async function checkReferralParam() {
            if (!userId) {
                return;
            }
            
            // Получаем параметры из startapp или ссылки Telegram
            const startApp = tg.initDataUnsafe.start_param;
            
            // Проверяем, содержит ли startApp реферальный параметр
            if (startApp && startApp.startsWith('ref=')) {
                const referrerId = startApp.replace('ref=', '');
                
                // Отправляем запрос на сервер для регистрации реферала
                try {
                    const response = await fetch('/api/user/referral-register', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Telegram-Init-Data': tg.initData || ''
                        },
                        body: JSON.stringify({ 
                            userId,
                            referrerId 
                        })
                    });
                    
                    if (response.ok) {
                        console.log('Referral registered successfully');
                    }
                } catch (error) {
                    console.error('Error registering referral:', error);
                }
            }
        }
        
        // Загрузка рейтинга игроков
        async function loadRanking() {
            if (!userId) {
                console.error('User ID not available for loading ranking');
                return;
            }
            
            try {
                const rankingList = document.getElementById('rankingList');
                rankingList.innerHTML = '<div class="ranking-list-loading"><i class="fas fa-spinner fa-spin"></i> Загрузка рейтинга...</div>';
                
                const response = await fetch('/api/ranking', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Telegram-Init-Data': tg.initData || ''
                    },
                    body: JSON.stringify({ 
                        userId,
                        username: username
                    })
                });
                
                if (!response.ok) {
                    throw new Error('Failed to load ranking data');
                }
                
                const data = await response.json();
                const topPlayers = data.topPlayers || [];
                const userRank = data.userRank || { rank: '--', totalUsers: '--' };
                
                // Обновляем ранг по балансу
                appState.balanceRank = userRank.rank;
                elements.balanceRankValue.textContent = userRank.rank;
                
                // Обновляем UI с рейтингом
                updateRankingUI(topPlayers, userRank);
                
            } catch (error) {
                console.error('Error loading ranking data:', error);
                document.getElementById('rankingList').innerHTML = 
                    '<div class="ranking-list-loading">Не удалось загрузить рейтинг. Попробуйте позже.</div>';
                document.getElementById('yourRank').textContent = '--';
            }
        }
        
        // Обновление UI рейтинга
        function updateRankingUI(topPlayers, userRank) {
            const rankingList = document.getElementById('rankingList');
            rankingList.innerHTML = '';
            
            if (!topPlayers || topPlayers.length === 0) {
                rankingList.innerHTML = '<div class="ranking-list-loading">Рейтинг пока пуст</div>';
                return;
            }
            
            topPlayers.forEach((player, index) => {
                const rankItem = document.createElement('div');
                let rankClass = '';
                
                if (index === 0) rankClass = 'ranking-top-1';
                else if (index === 1) rankClass = 'ranking-top-2';
                else if (index === 2) rankClass = 'ranking-top-3';
                
                if (player.userId == userId) {
                    rankClass += ' ranking-you';
                }
                
                const displayUsername = player.username && player.username !== 'user' ? 
                    player.username : `User${player.userId % 1000}`;
                
                rankItem.className = `ranking-item ${rankClass}`;
                rankItem.innerHTML = `
                    <div class="ranking-rank">${index + 1}</div>
                    <div class="ranking-username">@${displayUsername}</div>
                    <div class="ranking-balance">${formatNumber(player.balance)} $DGR</div>
                `;
                
                rankingList.appendChild(rankItem);
            });
            
            // Обновляем информацию о месте пользователя
            const yourRankElement = document.getElementById('yourRank');
            if (userRank && userRank.rank) {
                yourRankElement.textContent = `${userRank.rank} из ${userRank.totalUsers}`;
            } else {
                yourRankElement.textContent = '--';
            }
        }
        
        // Загрузка рейтинга по рефералам
        async function loadReferralRanking() {
            if (!userId) {
                console.error('User ID not available for loading referral ranking');
                return;
            }
            
            try {
                const rankingList = document.getElementById('referralRankingList');
                rankingList.innerHTML = '<div class="referral-ranking-list-loading"><i class="fas fa-spinner fa-spin"></i> Загрузка рейтинга...</div>';
                
                const response = await fetch('/api/ranking/referrals', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Telegram-Init-Data': tg.initData || ''
                    },
                    body: JSON.stringify({ 
                        userId,
                        username: username
                    })
                });
                
                if (!response.ok) {
                    throw new Error('Failed to load referral ranking data');
                }
                
                const data = await response.json();
                const topPlayers = data.topPlayers || [];
                const userRank = data.userRank || { rank: '--', totalUsers: '--' };
                
                // Обновляем ранг по рефералам
                appState.referralsRank = userRank.rank;
                elements.referralsRankValue.textContent = userRank.rank;
                
                // Обновляем UI с рейтингом
                updateReferralRankingUI(topPlayers, userRank);
                
            } catch (error) {
                console.error('Error loading referral ranking data:', error);
                document.getElementById('referralRankingList').innerHTML = 
                    '<div class="referral-ranking-list-loading">Не удалось загрузить рейтинг. Попробуйте позже.</div>';
                document.getElementById('yourReferralRank').textContent = '--';
            }
        }
        
        // Обновление UI рейтинга по рефералам
        function updateReferralRankingUI(topPlayers, userRank) {
            const rankingList = document.getElementById('referralRankingList');
            rankingList.innerHTML = '';
            
            if (!topPlayers || topPlayers.length === 0) {
                rankingList.innerHTML = '<div class="referral-ranking-list-loading">Рейтинг пока пуст</div>';
                return;
            }
            
            topPlayers.forEach((player, index) => {
                const rankItem = document.createElement('div');
                let rankClass = '';
                
                if (index === 0) rankClass = 'referral-ranking-top-1';
                else if (index === 1) rankClass = 'referral-ranking-top-2';
                else if (index === 2) rankClass = 'referral-ranking-top-3';
                
                if (player.userId == userId) {
                    rankClass += ' referral-ranking-you';
                }
                
                const displayUsername = player.username && player.username !== 'user' ? 
                    player.username : `User${player.userId % 1000}`;
                
                rankItem.className = `referral-ranking-item ${rankClass}`;
                rankItem.innerHTML = `
                    <div class="referral-ranking-rank">${index + 1}</div>
                    <div class="referral-ranking-username">@${displayUsername}</div>
                    <div class="referral-ranking-count">${formatNumber(player.referralCount)}</div>
                `;
                
                rankingList.appendChild(rankItem);
            });
            
            // Обновляем информацию о месте пользователя
            const yourRankElement = document.getElementById('yourReferralRank');
            if (userRank && userRank.rank) {
                yourRankElement.textContent = `${userRank.rank} из ${userRank.totalUsers}`;
            } else {
                yourRankElement.textContent = '--';
            }
        }
        
        // Функция для загрузки заданий
        async function loadTasks() {
            try {
                const response = await fetch('/api/tasks', {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                        'Telegram-Init-Data': tg.initData || ''
                    }
                });
                
                if (!response.ok) {
                    throw new Error('Failed to load tasks');
                }
                
                const tasks = await response.json();
                const tasksContainer = document.getElementById('tasksList');
                tasksContainer.innerHTML = '';
                
                tasks.forEach(task => {
                    const taskContainer = document.createElement('div');
                    taskContainer.className = 'task-button-container';
                    
                    taskContainer.innerHTML = `
                        <a href="${task.channel_link}" target="_blank" class="task-channel-btn">
                            <span class="task-channel-name">${task.title}</span>
                            <span class="task-reward">${task.reward} $DGR</span>
                        </a>
                        <button class="task-check-btn" onclick="checkTaskSubscription('${task.channel_id}', ${task.reward})">
                            Проверить
                        </button>
                    `;
                    
                    tasksContainer.appendChild(taskContainer);
                });
            } catch (error) {
                console.error('Error loading tasks:', error);
                showNotification('Ошибка при загрузке заданий');
            }
        }
        
        // Функция для проверки подписки на канал
        async function checkTaskSubscription(channelId, reward) {
            try {
                const checkBtn = event.target;
                checkBtn.disabled = true;
                checkBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
                
                const response = await fetch('/api/tasks/check-subscription', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Telegram-Init-Data': tg.initData || ''
                    },
                    body: JSON.stringify({
                        user_id: userId,
                        channel_id: channelId,
                        reward: reward
                    })
                });
                
                if (!response.ok) {
                    throw new Error('Failed to check subscription');
                }
                
                const data = await response.json();
                
                if (data.success) {
                    if (data.is_subscribed) {
                        showNotification(`Поздравляем! Вы получили ${reward} $DGR!`);
                        loadUserData(); // Обновляем баланс
                    } else {
                        showNotification('Вы еще не подписались на канал. Пожалуйста, подпишитесь и попробуйте снова.');
                    }
                } else {
                    showNotification(data.message || 'Ошибка при проверке подписки');
                }
            } catch (error) {
                console.error('Error checking subscription:', error);
                showNotification('Произошла ошибка при проверке подписки');
            } finally {
                if (event.target) {
                    event.target.disabled = false;
                    event.target.textContent = 'Проверить';
                }
            }
        }
        
        // Инициализация приложения
        async function initApp() {
            try {
                tg.ready();
                initMusic();
                await loadUserData();
                
                // Загружаем задания
                await loadTasks();
                
                // Загружаем реферальную статистику
                await loadReferralStats();
                
                // Проверяем реферальный параметр
                await checkReferralParam();
                
                // Обработчик для кнопки копирования ссылки
                document.getElementById('copyLinkBtn').addEventListener('click', copyReferralLink);
                
                // Обработчик для кнопки Claim
                document.getElementById('claimBtn').addEventListener('click', claimReferralEarnings);
                
                // Запускаем таймер для обновления времени до следующего claim
                startClaimTimer();
                
                setInterval(updateClicks, 1000);
                setInterval(loadUserData, 30000);
                
                // Обработчики навигации
                elements.mainBtn.addEventListener('click', () => switchPage('mainPage'));
                elements.tasksBtn.addEventListener('click', () => switchPage('tasksPage'));
                elements.profileBtn.addEventListener('click', () => switchPage('profilePage'));
                elements.friendsBtn.addEventListener('click', () => {
                    switchPage('friendsPage');
                    updateReferralUI(); // Обновляем реферальный UI при переключении на страницу
                });
                
                // Глобальный обработчик взаимодействия
                document.addEventListener('click', handleFirstInteraction, { once: true });
                
            } catch (error) {
                console.error('Initialization error:', error);
                showNotification('Ошибка инициализации приложения');
                setTimeout(initApp, 5000);
            }
        }
        
        // Запуск приложения
        document.addEventListener('DOMContentLoaded', initApp);
    </script>
</body>
</html>
