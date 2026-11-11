'use client';

import React, { useState, useEffect } from 'react';
import { Shell, NavigationTab } from '../components/Shell';
import { OverviewView } from '../components/OverviewView';
import { LiveTrackingView } from '../components/LiveTrackingView';
import { ShipmentsView } from '../components/ShipmentsView';
import { TemperatureView } from '../components/TemperatureView';
import { EvidenceView } from '../components/EvidenceView';
import { TimelineView } from '../components/TimelineView';
import { PaymentsView } from '../components/PaymentsView';
import { InvestigationsView } from '../components/InvestigationsView';
import { CarriersView } from '../components/CarriersView';
import { DemoCenterView } from '../components/DemoCenterView';
import { ReportsView } from '../components/ReportsView';
import { SettingsView } from '../components/SettingsView';
import { DEMO_SHIPMENTS, ShipmentModel } from '../lib/mockData';
import { api } from '../lib/api';

export default function ColdChainSentinelApp() {
  const [currentTab, setCurrentTab] = useState<NavigationTab>('overview');
  const [shipments, setShipments] = useState<ShipmentModel[]>(DEMO_SHIPMENTS);
  const [selectedShipment, setSelectedShipment] = useState<ShipmentModel>(DEMO_SHIPMENTS[0]);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isResetting, setIsResetting] = useState<boolean>(false);

  // Sync with live backend API when available
  useEffect(() => {
    let isMounted = true;

    async function fetchInitialData() {
      try {
        const liveShipments = await api.listShipments();
        if (isMounted && Array.isArray(liveShipments) && liveShipments.length > 0) {
          // Merge live backend data with rich mock coordinates if needed
          const merged = DEMO_SHIPMENTS.map((demo) => {
            const liveMatch = liveShipments.find((l: any) => l.tracking_number === demo.tracking_number);
            if (liveMatch) {
              return {
                ...demo,
                status: liveMatch.status || demo.status,
                payment_status: liveMatch.payment_status || demo.payment_status,
              };
            }
            return demo;
          });
          setShipments(merged);
        }
      } catch (err) {
        console.info('Backend initializing or offline — using robust local demo state:', err);
      }
    }

    fetchInitialData();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleSelectShipment = (shipment: ShipmentModel) => {
    setSelectedShipment(shipment);
  };

  const handleNavigateTab = (tab: any) => {
    // Map friendly alias to NavigationTab
    if (tab === 'live-tracking' || tab === 'map') {
      setCurrentTab('tracking');
    } else if (tab === 'telemetry') {
      setCurrentTab('temperature');
    } else {
      setCurrentTab(tab as NavigationTab);
    }
  };

  const handleResetScenarios = async () => {
    setIsResetting(true);
    try {
      await api.resetChallenge();
      setShipments([...DEMO_SHIPMENTS]);
      setSelectedShipment(DEMO_SHIPMENTS[0]);
    } catch (err) {
      console.warn('Backend reset call encountered error or offline mode, applying frontend state reset:', err);
      setShipments([...DEMO_SHIPMENTS]);
      setSelectedShipment(DEMO_SHIPMENTS[0]);
    } finally {
      setIsResetting(false);
    }
  };

  return (
    <Shell
      currentTab={currentTab}
      onSelectTab={setCurrentTab}
      onSearchChange={setSearchQuery}
      searchQuery={searchQuery}
      onResetScenarios={handleResetScenarios}
      isResetting={isResetting}
    >
      {currentTab === 'overview' && (
        <OverviewView
          shipments={shipments}
          onSelectShipment={handleSelectShipment}
          onNavigateTab={handleNavigateTab}
        />
      )}

      {currentTab === 'tracking' && (
        <LiveTrackingView
          shipments={shipments}
          selectedShipment={selectedShipment}
          onSelectShipment={handleSelectShipment}
          onNavigateTab={handleNavigateTab}
        />
      )}

      {currentTab === 'shipments' && (
        <ShipmentsView
          shipments={shipments}
          onSelectShipment={handleSelectShipment}
          onNavigateTab={handleNavigateTab}
        />
      )}

      {currentTab === 'temperature' && (
        <TemperatureView
          shipments={shipments}
          selectedShipment={selectedShipment}
          onSelectShipment={handleSelectShipment}
        />
      )}

      {currentTab === 'evidence' && <EvidenceView />}

      {currentTab === 'timeline' && <TimelineView />}

      {currentTab === 'payments' && <PaymentsView />}

      {currentTab === 'investigations' && <InvestigationsView />}

      {currentTab === 'carriers' && <CarriersView />}

      {currentTab === 'demo' && (
        <DemoCenterView
          onSelectShipment={handleSelectShipment}
          onNavigateTab={handleNavigateTab}
          onResetSuccess={() => {
            setShipments([...DEMO_SHIPMENTS]);
            setSelectedShipment(DEMO_SHIPMENTS[0]);
          }}
        />
      )}

      {currentTab === 'reports' && <ReportsView />}

      {currentTab === 'settings' && <SettingsView />}
    </Shell>
  );
}
