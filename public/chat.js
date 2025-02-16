(() => {
    let visible = false;
    const swapChatVisibility = () => {
      visible = !visible;
      document.getElementById("chatbase-bubble-window").style.display = (visible)? "flex" : "none";
    };
  
    const chatBubbleElement = document.createElement('div');
  
    chatBubbleElement.innerHTML = `<div id="chatbase-bubble-window" style="border: none; position: fixed; flex-direction: column; justify-content: space-between; box-shadow: rgba(150, 150, 150, 0.2) 0px 10px 30px 0px, rgba(150, 150, 150, 0.2) 0px 0px 0px 1px; bottom: 5rem; right: 1rem; width: 448px; height: 85dvh; max-height: 824px; border-radius: 0.75rem; display: none; z-index: 2147483646; overflow: hidden; background-color: white; left: unset; top: unset;"><div style="display: none; justify-content: center; height: 100%; align-items: center;"><svg viewBox="0 0 30 30" xmlns="http://www.w3.org/2000/svg" stroke="black" style="width:30px;height:30px;">
          <g>
              <rect x="11" y="1" width="2" height="5" opacity=".14"></rect>
              <rect x="11" y="1" width="1" height="5" transform="rotate(30 12 12)" opacity=".29"></rect>
              <rect x="11" y="1" width="1" height="5" transform="rotate(60 12 12)" opacity=".43"></rect>
              <rect x="11" y="1" width="1" height="5" transform="rotate(90 12 12)" opacity=".57"></rect>
              <rect x="11" y="1" width="1" height="5" transform="rotate(120 12 12)" opacity=".71"></rect>
              <rect x="11" y="1" width="1" height="5" transform="rotate(150 12 12)" opacity=".86"></rect>
              <rect x="11" y="1" width="1" height="5" transform="rotate(180 12 12)"></rect>
              <animateTransform attributeName="transform" type="rotate" calcMode="discrete" dur="0.75s" values="0 12 12;30 12 12;60 12 12;90 12 12;120 12 12;150 12 12;180 12 12;210 12 12;240 12 12;270 12 12;300 12 12;330 12 12;360 12 12" repeatCount="indefinite"></animateTransform>
          </g>
        </svg>
        </div>
          <iframe title="Chatbot" src="/public/chat.html" style="height: 100%; width: 100%; border: none; display: block;"></iframe></div>
          <div id="chat-bubble" style="display: flex; align-items: center; justify-content: center;position: fixed; border: 0px; bottom: 1rem; right: 1rem; width: 55px; height: 55px; border-radius: 27.5px; background-color: black; box-shadow: rgba(0, 0, 0, 0.2) 0px 4px 8px 0px; cursor: pointer; z-index: 2147483645; transition: 0.2s ease-in-out; left: unset; transform: scale(1);">
              <svg xmlns="http://www.w3.org/2000/svg" style="color: white; width: 2rem; height: 2rem; vertical-align: middle;" class="w-10 h-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
          </div>
  `;
    window.document.body.appendChild(chatBubbleElement);
    document.getElementById("chat-bubble").onclick = () => {
      swapChatVisibility();
    };
  })();