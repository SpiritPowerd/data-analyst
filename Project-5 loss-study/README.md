# Исследование убытков приложения


## Данные
<ol>
<li>Структура <code>visits_info_short.csv</code>:</li>
<ul>
<li><code>User Id</code> — уникальный идентификатор пользователя,</li>
<li><code>Region</code> — страна пользователя,</li>
<li><code>Device</code> — тип устройства пользователя,</li>
<li><code>Channel</code> — идентификатор источника перехода,</li>
<li><code>Session Start</code> — дата и время начала сессии,</li>
<li><code>Session End</code> — дата и время окончания сессии.</li>
</ul>
<li>Структура <code>orders_info_short.csv</code>:</li>
<ul>
<li><code>User Id</code> — уникальный идентификатор пользователя,</li>
<li><code>Event Dt</code> — дата и время покупки,</li>
<li><code>Revenue</code> — сумма заказа.</li>
</ul>
<li>Структура <code>costs_info_short.csv</code>:</li>
<ul>
<li><code>dt</code> — дата проведения рекламной кампании,</li>
<li><code>Channel</code> — идентификатор рекламного источника,</li>
<li><code>costs</code> — расходы на эту кампанию.</li>
</ul>
</ol>

## Задача

Разобраться в причине убытков и помочь компании выйти в плюс.

## Используемые библиотеки
<li><code>pandas</code></li>
<li><code>datetime</code></li>
<li><code>matplotlib.pyplot</code></li>
<li><code>numpy</code></li>