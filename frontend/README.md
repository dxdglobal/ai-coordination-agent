# Frontend - AI Coordination Agent

React + Vite frontend application for the AI Coordination Agent project management system.

## 🚀 Features

- **Modern React**: Built with React 18 and Vite for fast development and builds
- **Material-UI Design**: Beautiful, responsive UI using Material-UI components
- **Real-time Dashboard**: Interactive dashboard with project and task statistics
- **Task Management**: Comprehensive task creation, editing, and tracking
- **AI Chat Interface**: Direct chat with AI coordination agent
- **Integration Management**: Configure and test external service integrations
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices

## 📁 Project Structure

```
/frontend
├── index.html            # HTML entry point
├── package.json          # Dependencies and scripts
├── vite.config.js        # Vite configuration
├── .env.example         # Environment variables template
├── /src
│   ├── main.jsx         # React application entry point
│   ├── App.jsx          # Main application component with routing
│   ├── /components      # Reusable UI components
│   │   └── Navbar.jsx   # Navigation bar component
│   ├── /pages           # Main application pages
│   │   ├── Dashboard.jsx    # Dashboard with statistics and overview
│   │   ├── Projects.jsx     # Project management interface
│   │   ├── Tasks.jsx        # Task management interface
│   │   ├── Chat.jsx         # AI chat interface
│   │   └── Integrations.jsx # Integration configuration
│   └── /context         # React context providers
│       └── APIContext.jsx   # API client and state management
└── /public              # Static assets
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Ensure you're in the frontend directory
cd frontend

# Install Node.js dependencies
npm install
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# The default configuration should work for local development
# VITE_API_BASE_URL=http://localhost:5000
```

### 3. Start Development Server

```bash
npm run dev
# Frontend will be available at http://localhost:5173
```

## 🔧 Configuration

### Environment Variables

The frontend uses Vite environment variables (prefixed with `VITE_`):

```env
# API Configuration
VITE_API_BASE_URL=http://localhost:5000

# Optional: Additional configuration
VITE_APP_NAME=AI Coordination Agent
VITE_APP_VERSION=1.0.0
```

### API Integration

The frontend communicates with the Flask backend through the API context (`src/context/APIContext.jsx`). This provides:

- Centralized API client using Axios
- Error handling and user notifications
- Loading state management
- Authentication handling (if implemented)

## 🎨 UI Components

### Material-UI Theme

The application uses a custom Material-UI theme with:
- Primary color: Blue (#1976d2)
- Secondary color: Orange (#ff9800)
- Dark/Light mode support
- Responsive breakpoints
- Custom component styling

### Key Components

#### Navbar (`components/Navbar.jsx`)
- Application navigation
- Responsive mobile menu
- Active page highlighting
- Material-UI AppBar and Drawer

#### Dashboard (`pages/Dashboard.jsx`)
- Project and task statistics
- Recent activity display
- Quick action buttons
- Charts and data visualization

#### Projects Page (`pages/Projects.jsx`)
- Project listing with search and filters
- Project creation and editing forms
- Progress tracking and status management
- Project deletion with confirmation

#### Tasks Page (`pages/Tasks.jsx`)
- Comprehensive task management interface
- Advanced filtering (by project, status, assignee, search)
- Task creation with all fields (priority, deadline, estimates)
- Status updates and time tracking
- Comment system for task collaboration

#### AI Chat (`pages/Chat.jsx`)
- Interactive chat interface with AI agent
- Predefined prompt buttons for common operations
- Message history with timestamps
- Markdown support for AI responses
- Context-aware conversations

#### Integrations (`pages/Integrations.jsx`)
- Configuration interface for external services
- Test messaging functionality
- Integration history and status
- Service-specific settings and credentials

## 🔌 API Integration

### API Context

The `APIContext` provides methods for:

#### Projects API
```javascript
const { projects, createProject, updateProject, deleteProject } = useAPI();

// Create new project
await createProject({
  name: "New Project",
  description: "Project description",
  status: "active",
  deadline: "2024-12-31"
});
```

#### Tasks API
```javascript
const { tasks, createTask, updateTask, updateTaskStatus } = useAPI();

// Create new task
await createTask({
  title: "New Task",
  description: "Task description",
  status: "todo",
  priority: "medium",
  project_id: 1,
  assigned_to: "user@example.com",
  due_date: "2024-06-30"
});

// Update task status
await updateTaskStatus(taskId, "in_progress");
```

#### AI API
```javascript
const { sendChatMessage, analyzeWorkspace } = useAPI();

// Chat with AI
const response = await sendChatMessage("Analyze my current tasks");

// Analyze workspace
const analysis = await analyzeWorkspace();
```

#### Integration API
```javascript
const { sendWhatsAppMessage, sendTelegramMessage, sendEmail } = useAPI();

// Send WhatsApp message
await sendWhatsAppMessage({
  to: "+1234567890",
  message: "Task update notification"
});
```

## 🎯 Features Detail

### Dashboard Features
- **Project Statistics**: Total projects, active projects, completion rates
- **Task Statistics**: Total tasks, completed tasks, overdue tasks
- **Recent Activity**: Latest task updates and comments
- **Quick Actions**: Create project, create task, chat with AI
- **Visual Charts**: Progress charts and status distributions

### Task Management Features
- **Advanced Filtering**: Filter by multiple criteria simultaneously
- **Search Functionality**: Search across task titles and descriptions
- **Status Management**: Easy status updates with visual indicators
- **Priority System**: Visual priority indicators (high, medium, low)
- **Time Tracking**: Estimate vs. actual time spent tracking
- **Comment System**: Task-specific discussions and updates
- **Assignment Management**: Assign tasks to team members

### AI Chat Features
- **Natural Language Processing**: Chat naturally with the AI agent
- **Predefined Prompts**: Quick access to common AI operations
- **Context Awareness**: AI has access to current workspace data
- **Actionable Responses**: AI can suggest specific actions and improvements
- **Message History**: Persistent chat history within session

### Integration Features
- **Multi-Platform Support**: WhatsApp, Telegram, Email, Voice, Zendesk
- **Test Functionality**: Test each integration before using
- **Message History**: View sent messages and responses
- **Configuration Management**: Easy setup of API keys and settings

## 🛠️ Development

### Available Scripts

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint

# Run tests
npm run test
```

### Development Workflow

1. **Component Development**: Create reusable components in `/src/components`
2. **Page Development**: Add new pages in `/src/pages`
3. **API Integration**: Extend API context for new endpoints
4. **Styling**: Use Material-UI components and theme system
5. **Testing**: Add tests for new components and functionality

### Adding New Features

#### Adding a New Page
1. Create component in `/src/pages/NewPage.jsx`
2. Add route in `App.jsx`
3. Update navigation in `Navbar.jsx`
4. Add API methods if needed in `APIContext.jsx`

#### Adding New API Endpoints
1. Add method to `APIContext.jsx`
2. Handle errors and loading states
3. Update components to use new API method
4. Add error handling and user feedback

### Code Style and Conventions

- **React Hooks**: Use functional components with hooks
- **Material-UI**: Use Material-UI components for consistency
- **Error Handling**: Always handle API errors gracefully
- **Loading States**: Show loading indicators for async operations
- **Responsive Design**: Ensure all components work on mobile devices

## 📱 Responsive Design

The application is fully responsive and works on:
- **Desktop**: Full feature set with optimal layout
- **Tablet**: Adapted layouts with touch-friendly controls
- **Mobile**: Optimized for small screens with drawer navigation

### Breakpoints
- **xs**: 0px and up (mobile)
- **sm**: 600px and up (tablet)
- **md**: 900px and up (desktop)
- **lg**: 1200px and up (large desktop)
- **xl**: 1536px and up (extra large)

## 🎨 Theming and Customization

### Material-UI Theme

The theme can be customized in `App.jsx`:

```javascript
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2', // Custom primary color
    },
    secondary: {
      main: '#ff9800', // Custom secondary color
    },
  },
  components: {
    // Custom component overrides
  },
});
```

### Custom Styling

- Use Material-UI's `sx` prop for component-specific styling
- Create custom components in `/src/components`
- Follow Material Design principles

## 🚀 Deployment

### Build for Production

```bash
npm run build
```

This creates a `dist/` folder with optimized production files.

### Deployment Options

#### Static Hosting (Netlify, Vercel, AWS S3)
1. Build the project: `npm run build`
2. Upload the `dist/` folder contents
3. Configure environment variables in hosting platform
4. Set up redirects for single-page application

#### Docker Deployment
```dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Environment Configuration for Production

```env
# Production API URL
VITE_API_BASE_URL=https://your-api-domain.com

# Optional production settings
VITE_APP_NAME=AI Coordination Agent
VITE_ENVIRONMENT=production
```

## 🔧 Performance Optimization

### Bundle Optimization
- **Code Splitting**: Automatic route-based code splitting
- **Tree Shaking**: Unused code removal
- **Asset Optimization**: Image and asset compression
- **Lazy Loading**: Components loaded on demand

### Runtime Performance
- **React Memo**: Memoize expensive components
- **Virtual Scrolling**: For large lists (implement if needed)
- **Debounced Search**: Reduce API calls for search functionality
- **Caching**: API response caching where appropriate

## 🔒 Security Considerations

### Environment Variables
- Never commit `.env` files to version control
- Use VITE_ prefix for client-side environment variables
- Validate environment variables in production

### API Security
- Always validate API responses
- Handle authentication tokens securely
- Implement proper error boundaries
- Use HTTPS in production

### Content Security
- Sanitize user inputs
- Validate file uploads
- Implement proper CORS handling
- Use secure authentication methods

## 🧪 Testing

### Testing Framework
```bash
# Install testing dependencies
npm install --save-dev @testing-library/react @testing-library/jest-dom vitest

# Run tests
npm run test
```

### Test Structure
```
/tests
├── components/      # Component tests
├── pages/          # Page component tests
├── context/        # Context provider tests
└── utils/          # Utility function tests
```

### Testing Best Practices
- Test user interactions, not implementation details
- Use React Testing Library for DOM testing
- Mock API calls in tests
- Test accessibility features

## 🛠️ Troubleshooting

### Common Issues

#### Build Errors
- Clear node_modules and reinstall: `rm -rf node_modules package-lock.json && npm install`
- Check Node.js version compatibility
- Verify all dependencies are installed

#### API Connection Issues
- Verify backend server is running on correct port
- Check CORS configuration in backend
- Verify API base URL in environment variables

#### Development Server Issues
- Clear Vite cache: `rm -rf node_modules/.vite`
- Check port availability (default: 5173)
- Verify Vite configuration

### Performance Issues
- Use React DevTools Profiler to identify bottlenecks
- Implement React.memo for expensive components
- Optimize large list rendering with virtualization
- Check network tab for slow API calls

### Browser Compatibility
- The app supports modern browsers (Chrome 90+, Firefox 88+, Safari 14+)
- Use Babel polyfills if targeting older browsers
- Test on different devices and screen sizes

## 📚 Additional Resources

- [React Documentation](https://reactjs.org/docs)
- [Vite Documentation](https://vitejs.dev/guide/)
- [Material-UI Documentation](https://mui.com/getting-started/installation/)
- [React Router Documentation](https://reactrouter.com/web/guides/quick-start)
- [Axios Documentation](https://axios-http.com/docs/intro)
