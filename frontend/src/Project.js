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

    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [currentPage, setCurrentPage] = useState('main');
    const [username, setUsername] = useState(null);
    const [contentHeaders, setContentHeaders] = useState(["Code", "Description", "Value"]);
    const [fileHeaders, setFileHeaders] = useState(["Filename", "Type", "Total Pages", "Action"]);
    const [ruleFileHeaders, setRuleFileHeaders] = useState(["Regulation", "Action"]);
    const [complianceHeaders, setComplianceHeaders] = useState(["Requirement Statement", "Source", "Document Checklist Score", "Item Checklist Score", "Total Score", "# Equations Found", "Evidence"]);
    const [mathEquations, setMathEquations] = useState(["Requirement Statement", "Equation", "Output Variable", "Calculated When", "References"]);
    const navigate = useNavigate();



    const [searchParams] = useSearchParams();
    const applicationId = searchParams.get("application_id"); // Access ?file=yourfilename.pdf


    const [basicInfo, setBasicInfo] = useState(null);
    const [applicationName, setApplicationName] = useState(null);
    const [applicationContent, setApplicationContent] = useState([]);
    const [applicationLogs, setApplicationLogs] = useState([]);
    const [applicationFiles, setApplicationFiles] = useState([]);
    const [ruleFiles, setRuleFiles] = useState([]);
    const [rawComplianceResult, setRawComplianceResult] = useState([]);
    const [complianceResult, setComplianceResult] = useState([]);

    const [modalStateDoc, setModalStateDoc] = useState(null);
    const [modalContentDoc, setModalContentDoc] = useState([]);
    const [modalStateReq, setModalStateReq] = useState(null);
    const [modalContentReq, setModalContentReq] = useState([]);
    const [modalContentEq, setModalContentEq] = useState([]);

    const [loadingStatus, setLoadingStatus] = useState(false);



    useEffect(() => {
        const fetchApplicationData = async () => {
            try {

                setLoadingStatus(true);

                const responseApplication = await axios.get(BE_URL + "/get_application_detail?application_id=" + applicationId, {
                    application_id: applicationId
                });

                if (responseApplication.status === 200) {
                    console.log("response: ", responseApplication.data.compliance_check)
                    setBasicInfo(responseApplication.data.basic_info);
                    setApplicationContent(responseApplication.data.application_content);
                    setApplicationLogs(responseApplication.data.logs);
                    setApplicationFiles(responseApplication.data.files);
                    setRuleFiles(responseApplication.data.rule_files);

                    setRawComplianceResult(responseApplication.data.compliance_check);

                    setComplianceResult(responseApplication.data.compliance_check.map((item, idx) => ({
                        assessment_id: item.assessment_id,
                        requirement_source: item.requirement_source,
                        requirement_statement: item.requirement_statement,
                        document_checklist_score: (item.document_checklist_score * 100),
                        requirement_item_chek_score: (item.requirement_item_chek_score * 100),
                        total_score: (item.total_score * 100),
                        supporting_documents: item.supporting_documents,
                        requirement_items: item.requirement_items,
                        math_equations: item.math_equations,
                        action: (
                            <>
                                <Button kind="ghost" size="sm" renderIcon={Document} style={{ marginLeft: '1rem' }}
                                    onClick={() => setModalContentDoc((prevViewModalState) => ({
                                        ...prevViewModalState,
                                        [item.assessment_id + "_doc"]: true,
                                    }))}>Supp. Doc.</Button> |
                                <Button kind="ghost" size="sm" renderIcon={List} style={{ marginLeft: '1rem' }}
                                    onClick={() => setModalContentReq((prevViewModalState) => ({
                                        ...prevViewModalState,
                                        [item.assessment_id + "_req"]: true,
                                    }))}>Req. Items</Button> |
                                <Button kind="ghost" size="sm" renderIcon={Calculation} style={{ marginLeft: '1rem' }}
                                    onClick={() => setModalContentEq((prevViewModalState) => ({
                                        ...prevViewModalState,
                                        [item.assessment_id + "_eq"]: true,
                                    }))}>Math Eq.</Button>
                            </>
                        )
                    })));

                    responseApplication.data.compliance_check.map((item, index) => {
                        // console.log("compliance check", item);
                        setModalContentDoc((prevViewModalState) => ({
                            ...prevViewModalState,
                            [item.assessment_id + "_doc"]: false,
                        }));

                        setModalContentReq((prevViewModalState) => ({
                            ...prevViewModalState,
                            [item.assessment_id + "_req"]: false,
                        }));

                        setModalContentEq((prevViewModalState) => ({
                            ...prevViewModalState,
                            [item.assessment_id + "_eq"]: false,
                        }));
                    });




                }
            } catch (error) {
                console.log("error", error);
            }

            setLoadingStatus(false);
        };

        fetchApplicationData();
    }, []);

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
                    <BreadcrumbItem href="/project">Project Detail</BreadcrumbItem>
                </Breadcrumb>
            </div>
            <div className="overview" style={{ display: 'flex', justifyContent: 'center' }}>

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
                                            0000-0000
                                        </TableCell>
                                        <TableCell>
                                            RPS
                                        </TableCell>
                                        <TableCell>
                                            Forecast RPS
                                        </TableCell>
                                        <TableCell>
                                            2025-10-01 10:00:05
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