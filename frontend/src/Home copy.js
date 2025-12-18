import { Button, Tabs, Tab, TabList, TabPanels, TabPanel } from '@carbon/react';
import React, { useState, useEffect } from 'react';

import TradeOperationAssistant from './components/TradeOperationAssistant/TradeOperationAssistant'

import './Home.css'


import { useNavigate } from 'react-router-dom';
import axios from 'axios';

import HeaderBanner from './assets/header-banner.png'
import TextBanner from './assets/banner-with-text.png'

const server_host = `${process.env.REACT_APP_BE_API_URL}`;

function Home() {

  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState('main');
  const [username, setUsername] = useState(null);
  const navigate = useNavigate();


  useEffect(() => {
    
  }, []);

  return (
    <div>
      <div class="top-header">
        <img src={HeaderBanner} style={{ width: '100%' }} />
        <img src={TextBanner} style={{ width: '100%' }} />
      </div>

      <div style={{ paddingLeft: '150px', paddingRight: '150px',  marginTop: '3rem', marginBottom: '3rem', alignContent: 'center'}}>
          <Tabs>
              <TabList aria-label="Smart Assistant">
                  <Tab>Smart Assistant</Tab>
              </TabList>
              <TabPanels>
                  <TabPanel>
                      <TradeOperationAssistant />
                  </TabPanel>
              </TabPanels>
          </Tabs>
      </div>

      <div class="footer">
      Hak Cipta © 2024 Tigaraksa | All rights reserved
      </div>

    </div>
  );
}

export default Home;