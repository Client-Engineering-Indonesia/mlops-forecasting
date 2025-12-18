

import { useState, useEffect } from 'react';
import { ArrowRight, TextColor } from '@carbon/icons-react';
import axios from 'axios';
import { Button, TextInput, TextArea, Loading, ProgressBar, Form, Stack, NumberInput, FileUploader } from '@carbon/react';
import { Information, Reset, Send } from '@carbon/icons-react';
import '../../components/components.css'
import ChatHeader from '../../assets/chat-header.png'
import HomeIcon from '../../assets/home-icon.png'
import ResetIcon from '../../assets/reset-icon.png'
import SendButton from '../../assets/send-button.png'
import ChatbotAvatar from '../../assets/chatbot-avatar.png'
import UserAvatar from '../../assets/user-avatar.png'
import './TradeOperationAssistant.css'
import { marked } from "marked";
import DOMPurify from "dompurify";
import UploadForm from './UploadForm.js';
import './markdown.css'; // Custom CSS for Markdown


const BE_URL = 'http://127.0.0.1:8443/'

function TradeOperationAssistant() {
    const [uploadedFile, setUploadedFile] = useState(null);
    const [selectedFileType, setSelectedFileType] = useState(null);
    const [userInput, setUserInput] = useState('');
    const [chatContent, setChatContent] = useState([]);
    const [chatHistory, setChatHistory] = useState([]);
    const [loadingStatus, setLoadingStatus] = useState(false);
    const [uploadFormList, setUploadFormList] = useState([]);

    const resetUserInput = () => {
        setChatContent([]);
        setChatHistory([]);
    }

    const beautifyResponse = (resp) => {
        const rawHtml = marked(resp, { breaks: true });
        const cleanHtml = DOMPurify.sanitize(rawHtml); // Sanitize response to avoid XSS
        return cleanHtml;
    };

    const handleTextChange = (e) => setUserInput(e.target.value);

    const getFormattedDateTime = () => {
        const now = new Date();

        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, "0");
        const date = String(now.getDate()).padStart(2, "0");
        const hours = String(now.getHours()).padStart(2, "0");
        const minutes = String(now.getMinutes()).padStart(2, "0");
        const seconds = String(now.getSeconds()).padStart(2, "0");

        return `${year}-${month}-${date} ${hours}:${minutes}:${seconds}`;
    };

    async function chatStream(streamForm, usedInput, urlUsed) {
        const responseStream = await fetch(BE_URL + urlUsed, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            data: JSON.stringify(streamForm),
            body: JSON.stringify(streamForm)
        });

        if (!responseStream.body) {
            throw new Error("No response body");
        }

        const reader = responseStream.body.getReader();
        const decoder = new TextDecoder();
        let resultStream = "";

        const currentDate = getFormattedDateTime();
        setChatContent(prevChat => [...prevChat, {
            chatTime: currentDate,
            iconUsed: ChatbotAvatar,
            chatDetails: "",
            form: "false",
            imageUrls: [],
        }]);

        while (true) {
            setLoadingStatus(false);
            const { done, value } = await reader.read();
            if (done) break;
            resultStream += decoder.decode(value, { stream: true });

            console.log(resultStream);

            setChatContent((prevState) =>
                prevState.map((item, index) =>
                  index === prevState.length - 1 ? { ...item, chatDetails: resultStream } : item
                )
            );

            const scrollableWindow = document.querySelector('.chat-box');
            scrollableWindow.scrollTop = scrollableWindow.scrollHeight + 50; // Scroll to the bottom

        }

        setLoadingStatus(false);

        setChatHistory(prevHistory => [...prevHistory, {
            role: "user",
            content: usedInput
        }]);

        setChatHistory(prevHistory => [...prevHistory, {
            role: "assistant",
            content: resultStream
        }]);
    }

    const handleKeyDown = async (event) => {
        if (event.key === "Enter" && event.shiftKey) {
            event.preventDefault(); // Prevent default behavior
            console.log("Shift + Enter pressed:", userInput);
            setUserInput((prev) => prev + "\n"); // Add a new line to the text

        }
        else if (event.key === "Enter") {
          event.preventDefault(); // Prevent default Enter key behavior
          setUserInput('');
          // Call your function here
          //performAction(text);

          const currentDate = getFormattedDateTime();
          
          setChatContent(prevChat => [...prevChat, {
            chatTime: currentDate,
            iconUsed: UserAvatar,
            chatDetails: userInput,
            form: 'false',
            imageUrls: [],
          }]);

          const scrollableWindow = document.querySelector('.chat-box');
          scrollableWindow.scrollTop = scrollableWindow.scrollHeight + 50; // Scroll to the bottom
          setLoadingStatus(true);

          try {

            const responseForm = {
                text: userInput,
                chat_history: chatHistory
            }

            const response = await axios({
                method: 'post',
                url: BE_URL + "qna",
                headers: {
                    'Content-Type': 'application/json',
                    Accept: 'application/json',
                },
                data: JSON.stringify(responseForm)
            });

            if (response.status === 200) {
                const action = response.data.action;

                const currentDate2 = getFormattedDateTime();

                setChatContent(prevChat => [...prevChat, {
                    chatTime: currentDate2,
                    iconUsed: ChatbotAvatar,
                    chatDetails: response.data.result,
                    form: 'false',
                    imageUrls: [],
                }]);
            }

          } catch (error) {
            console.log(error);
          }

          setLoadingStatus(false);
          
        }
    };

    return (
        <div>
            <div class="content-layout">
                <div style={{padding: '20px'}}>
                <div class="chat-header">
                    <div class="chat-header-title">
                        <img src={HomeIcon} alt='Logo' style={{ paddingLeft: '1.5rem', width: 45, height: 'auto' }} />
                        <div class="chat-header-title-text">
                            Smart Assistant
                        </div>
                    </div>
                    <div class="chat-header-reset">
                    <Button kind="ghost" renderIcon={Reset} onClick={resetUserInput} />
                    </div>
                </div>

                <div class="chat-box">
                    <div class="chat-content">

                    {chatContent.length > 0 && (
                        
                        chatContent.map((item, index) => {
                            return (
                                <div>
                                    <div class="chat-content-response" style={{display: 'flex'}}>
                                        <div class="chat-content-response-1">
                                            
                                        <img src={item.iconUsed} alt='Logo' style={{ paddingRight: '1.5rem', width: 60, height: 'auto' }} />
                                        </div>
                                        <div class="chat-content-response-2">
                                            <div class="chat-content-response-time">
                                                {item.chatTime}
                                            </div>
                                            <div class="chat-content-response-text">
                                                <div
                                                dangerouslySetInnerHTML={{ __html: beautifyResponse(item.chatDetails) }}
                                                style={{ paddingRight: '1.5rem',whiteSpace: "pre-wrap", wordBreak: "break-word", overflowWrap: "break-word", width: "100%", maxWidth: "100%" }}
                                                />

                                                {item.form == 'true' && (
                                                    <UploadForm />
                                                )}

                                                {item.imageUrls.map((img, idx) => {

                                                return (
                                                    <div>
                                                        <img src={img} alt='Logo' style={{ paddingRight: '1.5rem', width: "800px", height: 'auto' }} />
                                                        <br />
                                                    </div>

                                                )
                                                })}
                                                
                                            </div>
                                        </div>

                                        

                                    </div>
                                    
                                </div>

                            )
                        })
                    )}

                    </div>

                    

                    {loadingStatus == true && (
                        <div>
                            <ProgressBar label="" withOverlay={false} style={{width: 40, height: 'auto', }} />
                        </div>
                    )}
                    
                    
                </div>

                <div class="chat-input">
                <TextArea disabled={loadingStatus} placeholder='Type your question here' value={userInput} onChange={handleTextChange} onKeyDown={handleKeyDown} />
                <div class="overlay-image">
                <Button kind="ghost" renderIcon={Send} />
                </div>
                
                </div>

                <div class="chat-footer">
                Built with &nbsp; <b class="bold">IBM watsonx</b> &nbsp; <Information title="Close" size={16} />
                </div>

                </div>
            </div>
        </div>
    )
}

export default TradeOperationAssistant;

