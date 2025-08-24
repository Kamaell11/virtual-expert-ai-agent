import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Container,
  Grid,
  Paper,
  Chip,
  Button,
  CircularProgress,
} from '@mui/material';
import {
  Chat,
  History,
  SmartToy,
  TrendingUp,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { queryAPI, systemAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    totalQueries: 0,
    recentQueries: [],
    systemStatus: 'checking',
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [queriesResponse, systemInfo] = await Promise.all([
          queryAPI.getQueries(0, 20),
          systemAPI.healthCheck().catch(() => ({ status: 'error', services: {} })),
        ]);

        console.log('Dashboard queries response:', queriesResponse); // Debug log
        
        // Handle API response format - queries are in .queries property
        const queriesData = queriesResponse.queries || queriesResponse || [];
        
        setStats({
          totalQueries: queriesData.length,
          recentQueries: queriesData.slice(0, 3),
          systemStatus: systemInfo.status === 'healthy' ? 'online' : systemInfo.status || 'error',
        });
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
        setStats(prev => ({ ...prev, systemStatus: 'error' }));
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
    
    // Auto-refresh every 30 seconds
    const intervalId = setInterval(fetchDashboardData, 30000);
    
    // Cleanup interval on component unmount
    return () => clearInterval(intervalId);
  }, []);

  const getSystemStatusColor = (status) => {
    switch (status) {
      case 'online':
        return 'success';
      case 'offline':
        return 'error';
      case 'checking':
        return 'info';
      default:
        return 'warning';
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Dashboard
        </Typography>
        <Typography variant="body1" color="textSecondary">
          Welcome back, {user?.username}! Here's your AI assistant overview.
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Quick Stats */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Chat color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Total Queries</Typography>
              </Box>
              <Typography variant="h4" color="primary">
                {stats.totalQueries}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <SmartToy color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">AI Status</Typography>
              </Box>
              <Chip
                label={stats.systemStatus.charAt(0).toUpperCase() + stats.systemStatus.slice(1)}
                color={getSystemStatusColor(stats.systemStatus)}
                variant="outlined"
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <TrendingUp color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">This Session</Typography>
              </Box>
              <Typography variant="h4" color="primary">
                {stats.recentQueries.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <History color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Recent Activity</Typography>
              </Box>
              <Typography variant="h4" color="primary">
                {stats.recentQueries.length > 0 ? 'Active' : 'None'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
                <Button
                  variant="contained"
                  startIcon={<Chat />}
                  onClick={() => navigate('/chat')}
                  fullWidth
                >
                  Start New Chat
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<History />}
                  onClick={() => navigate('/history')}
                  fullWidth
                >
                  View Chat History
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Conversations */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Conversations
              </Typography>
              {stats.recentQueries.length > 0 ? (
                <Box sx={{ mt: 2 }}>
                  {stats.recentQueries.map((query, index) => (
                    <Paper
                      key={query.id || index}
                      elevation={0}
                      sx={{
                        p: 2,
                        mb: 1,
                        backgroundColor: 'grey.50',
                        cursor: 'pointer',
                        '&:hover': {
                          backgroundColor: 'grey.100',
                        },
                      }}
                      onClick={() => navigate('/history')}
                    >
                      <Typography variant="body2" noWrap>
                        {query.query_text || query.text || 'Previous conversation'}
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        {query.timestamp ? new Date(query.timestamp).toLocaleString() : 'Recent'}
                      </Typography>
                    </Paper>
                  ))}
                </Box>
              ) : (
                <Box
                  sx={{
                    textAlign: 'center',
                    py: 4,
                    color: 'text.secondary',
                  }}
                >
                  <SmartToy sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />
                  <Typography variant="body2">
                    No recent conversations yet.
                  </Typography>
                  <Button
                    variant="text"
                    onClick={() => navigate('/chat')}
                    sx={{ mt: 1 }}
                  >
                    Start your first chat
                  </Button>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Welcome Message */}
        <Grid item xs={12}>
          <Card sx={{ backgroundColor: 'primary.main', color: 'primary.contrastText' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Virtual Expert AI Assistant
              </Typography>
              <Typography variant="body1">
                Your intelligent assistant is ready to help you with questions, analysis, and problem-solving. 
                Start a conversation to explore the capabilities of advanced language models.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;