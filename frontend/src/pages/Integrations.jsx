import React, { useState, useEffect } from 'react'
import {
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Box,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Chip,
  Paper,
  Tabs,
  Tab,
  LinearProgress,
  IconButton,
  Tooltip,
} from '@mui/material'
import {
  WhatsApp,
  Telegram,
  Email,
  Mic,
  Send,
  Refresh,
  History,
  Settings,
  IntegrationInstructions,
} from '@mui/icons-material'
import { useAPI } from '../context/APIContext'

const TabPanel = ({ children, value, index, ...other }) => (
  <div
    role="tabpanel"
    hidden={value !== index}
    id={`integration-tabpanel-${index}`}
    aria-labelledby={`integration-tab-${index}`}
    {...other}
  >
    {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
  </div>
)

const Integrations = () => {
  const { integrationsAPI, loading, error, setError } = useAPI()
  const [activeTab, setActiveTab] = useState(0)
  const [history, setHistory] = useState([])
  const [openSendDialog, setOpenSendDialog] = useState(false)
  const [selectedPlatform, setSelectedPlatform] = useState('')
  const [messageForm, setMessageForm] = useState({
    recipient: '',
    subject: '',
    message: '',
  })

  const integrationPlatforms = [
    {
      name: 'WhatsApp',
      icon: <WhatsApp sx={{ color: '#25D366' }} />,
      description: 'Send and receive WhatsApp messages',
      platform: 'whatsapp',
      connected: true,
    },
    {
      name: 'Telegram',
      icon: <Telegram sx={{ color: '#0088cc' }} />,
      description: 'Bot integration for Telegram notifications',
      platform: 'telegram',
      connected: true,
    },
    {
      name: 'Email',
      icon: <Email sx={{ color: '#ea4335' }} />,
      description: 'Send email notifications and updates',
      platform: 'email',
      connected: true,
    },
    {
      name: 'Voice',
      icon: <Mic sx={{ color: '#ff9800' }} />,
      description: 'Voice commands and transcription',
      platform: 'voice',
      connected: true,
    },
    {
      name: 'Zendesk',
      icon: <IntegrationInstructions sx={{ color: '#03363d' }} />,
      description: 'Customer support ticket integration',
      platform: 'zendesk',
      connected: false,
    },
  ]

  useEffect(() => {
    loadIntegrationHistory()
  }, [activeTab])

  const loadIntegrationHistory = async () => {
    try {
      const filters = {}
      if (activeTab > 0) {
        filters.platform = integrationPlatforms[activeTab - 1]?.platform
      }
      const data = await integrationsAPI.getHistory(filters)
      setHistory(data)
    } catch (err) {
      console.error('Failed to load integration history:', err)
    }
  }

  const handleSendMessage = async () => {
    try {
      let result
      
      switch (selectedPlatform) {
        case 'whatsapp':
          result = await integrationsAPI.sendWhatsApp(
            messageForm.recipient,
            messageForm.message
          )
          break
        case 'telegram':
          result = await integrationsAPI.sendTelegram(
            messageForm.recipient,
            messageForm.message
          )
          break
        case 'email':
          result = await integrationsAPI.sendEmail(
            messageForm.recipient,
            messageForm.subject,
            messageForm.message
          )
          break
        default:
          throw new Error('Invalid platform selected')
      }

      setOpenSendDialog(false)
      resetMessageForm()
      await loadIntegrationHistory()
      
      // Show success message
      setError(null)
    } catch (err) {
      console.error('Failed to send message:', err)
    }
  }

  const resetMessageForm = () => {
    setMessageForm({
      recipient: '',
      subject: '',
      message: '',
    })
  }

  const openSendMessageDialog = (platform) => {
    setSelectedPlatform(platform)
    resetMessageForm()
    setOpenSendDialog(true)
  }

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString()
  }

  const getPlatformIcon = (platform) => {
    const platformConfig = integrationPlatforms.find(p => p.platform === platform)
    return platformConfig?.icon || <IntegrationInstructions />
  }

  const getPlatformColor = (platform) => {
    switch (platform) {
      case 'whatsapp': return '#25D366'
      case 'telegram': return '#0088cc'
      case 'email': return '#ea4335'
      case 'voice': return '#ff9800'
      case 'zendesk': return '#03363d'
      default: return '#666'
    }
  }

  if (loading) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ width: '100%', mt: 2 }}>
          <LinearProgress />
        </Box>
      </Container>
    )
  }

  return (
    <Container maxWidth="lg">
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Integrations</Typography>
        <Button
          variant="contained"
          startIcon={<Refresh />}
          onClick={loadIntegrationHistory}
        >
          Refresh
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Integration Platform Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {integrationPlatforms.map((platform) => (
          <Grid item xs={12} sm={6} md={4} key={platform.platform}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Avatar sx={{ mr: 2, bgcolor: 'transparent' }}>
                    {platform.icon}
                  </Avatar>
                  <Box>
                    <Typography variant="h6">{platform.name}</Typography>
                    <Chip
                      label={platform.connected ? 'Connected' : 'Not Connected'}
                      color={platform.connected ? 'success' : 'default'}
                      size="small"
                    />
                  </Box>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  {platform.description}
                </Typography>
              </CardContent>
              <CardActions>
                {platform.connected ? (
                  <>
                    <Button
                      size="small"
                      startIcon={<Send />}
                      onClick={() => openSendMessageDialog(platform.platform)}
                      disabled={platform.platform === 'voice' || platform.platform === 'zendesk'}
                    >
                      Send Message
                    </Button>
                    <Button size="small" startIcon={<Settings />}>
                      Configure
                    </Button>
                  </>
                ) : (
                  <Button size="small" variant="contained">
                    Connect
                  </Button>
                )}
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Integration History */}
      <Paper>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs
            value={activeTab}
            onChange={(e, newValue) => setActiveTab(newValue)}
            aria-label="integration history tabs"
          >
            <Tab label="All Messages" />
            {integrationPlatforms.map((platform) => (
              <Tab key={platform.platform} label={platform.name} />
            ))}
          </Tabs>
        </Box>

        <TabPanel value={activeTab} index={0}>
          <Typography variant="h6" gutterBottom>
            All Integration Messages
          </Typography>
          <List>
            {history.length === 0 ? (
              <ListItem>
                <ListItemText primary="No messages found" />
              </ListItem>
            ) : (
              history.map((message) => (
                <ListItem key={message.id} divider>
                  <ListItemAvatar>
                    <Avatar sx={{ bgcolor: getPlatformColor(message.platform) }}>
                      {getPlatformIcon(message.platform)}
                    </Avatar>
                  </ListItemAvatar>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <Chip label={message.platform} size="small" />
                        <Typography variant="caption">
                          {formatTimestamp(message.created_at)}
                        </Typography>
                        {message.sender && (
                          <Typography variant="caption">
                            From: {message.sender}
                          </Typography>
                        )}
                        {message.recipient && (
                          <Typography variant="caption">
                            To: {message.recipient}
                          </Typography>
                        )}
                      </Box>
                    }
                    secondary={
                      <Typography variant="body2" sx={{ mt: 1 }}>
                        {message.content || 'No content'}
                      </Typography>
                    }
                  />
                </ListItem>
              ))
            )}
          </List>
        </TabPanel>

        {integrationPlatforms.map((platform, index) => (
          <TabPanel key={platform.platform} value={activeTab} index={index + 1}>
            <Typography variant="h6" gutterBottom>
              {platform.name} Messages
            </Typography>
            <List>
              {history
                .filter(msg => msg.platform === platform.platform)
                .map((message) => (
                  <ListItem key={message.id} divider>
                    <ListItemAvatar>
                      <Avatar sx={{ bgcolor: getPlatformColor(message.platform) }}>
                        {platform.icon}
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                          <Typography variant="caption">
                            {formatTimestamp(message.created_at)}
                          </Typography>
                          {message.sender && (
                            <Typography variant="caption">
                              From: {message.sender}
                            </Typography>
                          )}
                          {message.recipient && (
                            <Typography variant="caption">
                              To: {message.recipient}
                            </Typography>
                          )}
                        </Box>
                      }
                      secondary={
                        <Typography variant="body2" sx={{ mt: 1 }}>
                          {message.content || 'No content'}
                        </Typography>
                      }
                    />
                  </ListItem>
                ))}
              {history.filter(msg => msg.platform === platform.platform).length === 0 && (
                <ListItem>
                  <ListItemText primary={`No ${platform.name} messages found`} />
                </ListItem>
              )}
            </List>
          </TabPanel>
        ))}
      </Paper>

      {/* Send Message Dialog */}
      <Dialog open={openSendDialog} onClose={() => setOpenSendDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          Send {integrationPlatforms.find(p => p.platform === selectedPlatform)?.name} Message
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label={selectedPlatform === 'telegram' ? 'Chat ID' : 
                   selectedPlatform === 'whatsapp' ? 'Phone Number' : 'Email Address'}
            fullWidth
            variant="outlined"
            value={messageForm.recipient}
            onChange={(e) => setMessageForm({ ...messageForm, recipient: e.target.value })}
            sx={{ mb: 2 }}
            placeholder={selectedPlatform === 'telegram' ? 'e.g., 123456789' :
                        selectedPlatform === 'whatsapp' ? 'e.g., +1234567890' : 'e.g., user@example.com'}
          />

          {selectedPlatform === 'email' && (
            <TextField
              margin="dense"
              label="Subject"
              fullWidth
              variant="outlined"
              value={messageForm.subject}
              onChange={(e) => setMessageForm({ ...messageForm, subject: e.target.value })}
              sx={{ mb: 2 }}
            />
          )}

          <TextField
            margin="dense"
            label="Message"
            fullWidth
            multiline
            rows={4}
            variant="outlined"
            value={messageForm.message}
            onChange={(e) => setMessageForm({ ...messageForm, message: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenSendDialog(false)}>Cancel</Button>
          <Button
            onClick={handleSendMessage}
            variant="contained"
            disabled={!messageForm.recipient || !messageForm.message}
          >
            Send
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  )
}

export default Integrations