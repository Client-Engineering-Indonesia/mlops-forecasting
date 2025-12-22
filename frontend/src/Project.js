import {
    Breadcrumb,
    BreadcrumbItem,
    TextInput,
    TextArea,
    Form,
    Stack,
    FormGroup,
    Button,
    Link,
    Modal,
    UnorderedList,
    ListItem,
    Table,
    TableHead,
    TableRow,
    TableHeader,
    TableBody,
    TableCell,
    Tabs,
    TabList,
    Tab,
    TabPanels,
    TabPanel,
    Loading,
    unstable__IconIndicator as IconIndicator,
    Callout,
} from '@carbon/react';
import React, { useState, useEffect } from 'react';
import { Add, View, AiLaunch, ImageSearchAlt, AiGenerate, Notification, Document, List, Calculation } from '@carbon/icons-react';
import { useSearchParams } from "react-router-dom";


import './Home.css';
import './Project.css';



import { useNavigate } from 'react-router-dom';
import axios from 'axios';

import HeaderBanner from './assets/top-nav.png'
import IBMLogo from './assets/ibm-logo.png'
import TextBanner from './assets/Banner-Only.png'
import OverviewBanner from './assets/overview-banner.png'
import LCOVerviewImg from './assets/lc-overview-img.png'

import Datasets from './components/Datasets/Datasets'
import Features from './components/Features/Features'
import Models from './components/Models/Models'
import Predictions from './components/Predictions/Predictions'



function Project() {

    const BE_URL = process.env.REACT_APP_API_URL;

    const navigate = useNavigate();

    const [searchParams] = useSearchParams();
    const projectId = searchParams.get("project_id"); // Access ?file=yourfilename.pdf

    const [projects, setProjects] = useState([]);
    const [error, setError] = useState(null);

    const [loading, setLoading] = useState(false);

    async function getProject() {
        setLoading(true);
        const response = await fetch(BE_URL + "/get_project_by_projectid?project_id=" + projectId);

        if (!response.ok) {
        throw new Error("Failed to fetch projects");
        }

        setLoading(false);

        return await response.json();
    }
    
    useEffect(() => {
        getProject()
          .then(setProjects)
          .catch(err => setError(err.message));
      }, []);
    
      if (error) return <p>Error: {error}</p>;

    return (
        <div className="main-page">
            <div className="top-header">
                <img src={HeaderBanner} alt="Header" className="header-banner" />
                <div className="header-sub">
                    <img src={IBMLogo} alt="Logo" className="overlay-logo" />
                    <span className="header-sub-text">Smart Forecasting Tool</span>
                </div>
                <div className="header-overlay">
                    <h1 className="header-title">Faster <span className='header-title-span'>Forecasting Model Development Lifecycle</span> with AI-Embedded Capability</h1>
                </div>

                <img src={TextBanner} style={{ width: '100%', marginTop: '-10px' }} />

            </div>
            <div className="breadcrumb">
                <Breadcrumb>
                    <BreadcrumbItem href="/home">Home</BreadcrumbItem>
                    <BreadcrumbItem href={`/project?project_id=${projectId}`}>Project Detail</BreadcrumbItem>
                </Breadcrumb>
            </div>
            <div className="overview" style={{ display: 'flex', justifyContent: 'center' }}>

                {loading == true && (
                    <Loading
                        active
                        className="some-class"
                        description="Loading"
                        withOverlay={loading}
                    />
                )}

                <div className='form-group'>

                    <h2>PROJECT DETAILS</h2>

                    <Form>
                        <Stack gap={7}>
                            <Table
                                aria-label="sample table"
                                size="lg"
                            >
                                <TableHead>
                                    <TableRow>
                                        <TableHeader>
                                            ID
                                        </TableHeader>
                                        <TableHeader>
                                            Name
                                        </TableHeader>
                                        <TableHeader>
                                            Description
                                        </TableHeader>
                                        <TableHeader>
                                            Creation Time
                                        </TableHeader>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    <TableRow>
                                        <TableCell>
                                            {projects.project_id}
                                        </TableCell>
                                        <TableCell>
                                            {projects.project_name}
                                        </TableCell>
                                        <TableCell>
                                            {projects.project_description}
                                        </TableCell>
                                        <TableCell>
                                            {projects.creation_date}
                                        </TableCell>
                                    </TableRow>
                                </TableBody>
                            </Table>

                            <div style={{ paddingLeft: '150px', paddingRight: '150px', marginTop: '3rem', marginBottom: '3rem', alignContent: 'center' }}>

                                <Tabs>
                                    <TabList aria-label="Tigaraksa Assistant">
                                        <Tab>Datasets</Tab>
                                        <Tab>Features</Tab>
                                        <Tab>Models</Tab>
                                        <Tab>Predictions</Tab>
                                    </TabList>
                                    <TabPanels>

                                        <TabPanel class="tab-page">
                                            <Datasets />
                                        </TabPanel>
                                        <TabPanel class="tab-page">
                                            <Features />
                                        </TabPanel>
                                        <TabPanel class="tab-page">
                                            <Models />
                                        </TabPanel>
                                        <TabPanel class="tab-page">
                                            <Predictions />
                                        </TabPanel>
                                    </TabPanels>
                                </Tabs>

                            </div>

                        </Stack>

                    </Form>
                </div>
            </div>


            <div class="footer">
                Copyright © IBM Corporation 2025
            </div>

        </div>
    );
}

export default Project;